"""
Liquipedia数据获取服务
用于从Liquipedia Wiki获取战队、选手、锦标赛信息
"""

import requests
import time
import json
import re
from datetime import datetime
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

class LiquipediaService:
    """Liquipedia数据获取服务"""
    
    def __init__(self, rate_limit_delay: float = 1.0):
        """
        初始化Liquipedia服务
        
        Args:
            rate_limit_delay: 请求间隔（秒），避免被限流
        """
        self.base_url = "https://liquipedia.net/dota2"
        self.api_url = "https://liquipedia.net/dota2/api.php"
        self.rate_limit_delay = rate_limit_delay
        
        # 设置请求头，模拟浏览器访问
        self.headers = {
            'User-Agent': 'DotaAnalysis/1.0 (https://github.com/dotaanalysis; contact@dotaanalysis.com)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def _make_request(self, url: str, params: Dict = None) -> Optional[requests.Response]:
        """发送请求"""
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            # 控制请求频率
            time.sleep(self.rate_limit_delay)
            
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Liquipedia请求失败: {e}")
            return None
    
    def get_team_info(self, team_name: str) -> Optional[Dict]:
        """
        获取战队信息
        
        Args:
            team_name: 战队名称
            
        Returns:
            战队信息字典或None
        """
        try:
            # 构建战队页面URL
            team_url = f"{self.base_url}/{team_name.replace(' ', '_')}"
            
            response = self._make_request(team_url)
            if not response:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            team_info = {
                'name': team_name,
                'url': team_url,
                'logo_url': None,
                'region': None,
                'founded_date': None,
                'disbanded_date': None,
                'total_earnings': None,
                'current_roster': [],
                'former_players': [],
                'achievements': [],
                'social_links': {},
                'description': None
            }
            
            # 提取Logo
            logo_img = soup.find('img', class_='team-template-image')
            if logo_img and logo_img.get('src'):
                team_info['logo_url'] = f"https://liquipedia.net{logo_img['src']}"
            
            # 提取基本信息表格
            infobox = soup.find('div', class_='fo-nttax-infobox')
            if infobox:
                # 地区信息
                region_row = infobox.find('div', string=re.compile(r'Location|Region'))
                if region_row:
                    region_cell = region_row.find_next_sibling()
                    if region_cell:
                        team_info['region'] = region_cell.get_text(strip=True)
                
                # 成立日期
                founded_row = infobox.find('div', string=re.compile(r'Founded|Created'))
                if founded_row:
                    founded_cell = founded_row.find_next_sibling()
                    if founded_cell:
                        team_info['founded_date'] = founded_cell.get_text(strip=True)
                
                # 解散日期
                disbanded_row = infobox.find('div', string=re.compile(r'Disbanded|Inactive'))
                if disbanded_row:
                    disbanded_cell = disbanded_row.find_next_sibling()
                    if disbanded_cell:
                        team_info['disbanded_date'] = disbanded_cell.get_text(strip=True)
                
                # 总奖金
                earnings_row = infobox.find('div', string=re.compile(r'Approx. Total Winnings'))
                if earnings_row:
                    earnings_cell = earnings_row.find_next_sibling()
                    if earnings_cell:
                        earnings_text = earnings_cell.get_text(strip=True)
                        # 提取数字
                        earnings_match = re.search(r'\$?([\d,]+)', earnings_text)
                        if earnings_match:
                            team_info['total_earnings'] = earnings_match.group(1).replace(',', '')
            
            # 提取当前阵容
            roster_section = soup.find('span', {'id': 'Active_Roster'})
            if not roster_section:
                roster_section = soup.find('span', {'id': 'Current_Roster'})
            
            if roster_section:
                roster_table = roster_section.find_next('table', class_='wikitable')
                if roster_table:
                    rows = roster_table.find_all('tr')[1:]  # 跳过表头
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 2:
                            player_info = {
                                'id': cells[0].get_text(strip=True),
                                'name': cells[1].get_text(strip=True),
                                'position': cells[2].get_text(strip=True) if len(cells) > 2 else None,
                                'join_date': cells[3].get_text(strip=True) if len(cells) > 3 else None
                            }
                            team_info['current_roster'].append(player_info)
            
            # 提取社交链接
            links_section = soup.find('div', class_='infobox-links')
            if links_section:
                links = links_section.find_all('a')
                for link in links:
                    href = link.get('href', '')
                    text = link.get_text(strip=True).lower()
                    
                    if 'twitter' in href:
                        team_info['social_links']['twitter'] = href
                    elif 'facebook' in href:
                        team_info['social_links']['facebook'] = href
                    elif 'youtube' in href:
                        team_info['social_links']['youtube'] = href
                    elif 'twitch' in href:
                        team_info['social_links']['twitch'] = href
            
            # 提取描述
            content_div = soup.find('div', {'id': 'mw-content-text'})
            if content_div:
                first_paragraph = content_div.find('p')
                if first_paragraph:
                    team_info['description'] = first_paragraph.get_text(strip=True)[:500]  # 限制长度
            
            return team_info
            
        except Exception as e:
            logger.error(f"获取战队信息失败 {team_name}: {e}")
            return None
    
    def get_tournament_info(self, tournament_name: str) -> Optional[Dict]:
        """
        获取锦标赛信息
        
        Args:
            tournament_name: 锦标赛名称
            
        Returns:
            锦标赛信息字典或None
        """
        try:
            tournament_url = f"{self.base_url}/{tournament_name.replace(' ', '_')}"
            
            response = self._make_request(tournament_url)
            if not response:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            tournament_info = {
                'name': tournament_name,
                'url': tournament_url,
                'logo_url': None,
                'start_date': None,
                'end_date': None,
                'prize_pool': None,
                'location': None,
                'organizer': None,
                'participants': [],
                'results': {},
                'format': None
            }
            
            # 提取Logo
            logo_img = soup.find('img', class_='tournament-image')
            if logo_img and logo_img.get('src'):
                tournament_info['logo_url'] = f"https://liquipedia.net{logo_img['src']}"
            
            # 提取基本信息
            infobox = soup.find('div', class_='fo-nttax-infobox')
            if infobox:
                # 奖金池
                prize_row = infobox.find('div', string=re.compile(r'Prize Pool'))
                if prize_row:
                    prize_cell = prize_row.find_next_sibling()
                    if prize_cell:
                        prize_text = prize_cell.get_text(strip=True)
                        prize_match = re.search(r'\$?([\d,]+)', prize_text)
                        if prize_match:
                            tournament_info['prize_pool'] = prize_match.group(1).replace(',', '')
                
                # 日期
                date_row = infobox.find('div', string=re.compile(r'Start Date|Date'))
                if date_row:
                    date_cell = date_row.find_next_sibling()
                    if date_cell:
                        tournament_info['start_date'] = date_cell.get_text(strip=True)
                
                end_date_row = infobox.find('div', string=re.compile(r'End Date'))
                if end_date_row:
                    end_date_cell = end_date_row.find_next_sibling()
                    if end_date_cell:
                        tournament_info['end_date'] = end_date_cell.get_text(strip=True)
                
                # 地点
                location_row = infobox.find('div', string=re.compile(r'Location|Venue'))
                if location_row:
                    location_cell = location_row.find_next_sibling()
                    if location_cell:
                        tournament_info['location'] = location_cell.get_text(strip=True)
                
                # 主办方
                organizer_row = infobox.find('div', string=re.compile(r'Organizer'))
                if organizer_row:
                    organizer_cell = organizer_row.find_next_sibling()
                    if organizer_cell:
                        tournament_info['organizer'] = organizer_cell.get_text(strip=True)
            
            # 提取参赛队伍
            participants_section = soup.find('span', {'id': 'Participants'})
            if participants_section:
                participants_div = participants_section.find_next('div', class_='teamcard')
                if participants_div:
                    team_cards = participants_div.find_all('div', class_='teamcard-inner')
                    for card in team_cards:
                        team_name_elem = card.find('div', class_='teamcard-text')
                        if team_name_elem:
                            tournament_info['participants'].append({
                                'name': team_name_elem.get_text(strip=True)
                            })
            
            return tournament_info
            
        except Exception as e:
            logger.error(f"获取锦标赛信息失败 {tournament_name}: {e}")
            return None
    
    def get_player_info(self, player_name: str) -> Optional[Dict]:
        """
        获取选手信息
        
        Args:
            player_name: 选手名称或ID
            
        Returns:
            选手信息字典或None
        """
        try:
            player_url = f"{self.base_url}/{player_name.replace(' ', '_')}"
            
            response = self._make_request(player_url)
            if not response:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            player_info = {
                'name': player_name,
                'url': player_url,
                'real_name': None,
                'country': None,
                'birth_date': None,
                'current_team': None,
                'position': None,
                'total_earnings': None,
                'team_history': [],
                'achievements': [],
                'social_links': {}
            }
            
            # 提取基本信息
            infobox = soup.find('div', class_='fo-nttax-infobox')
            if infobox:
                # 真实姓名
                name_row = infobox.find('div', string=re.compile(r'Name|Real Name'))
                if name_row:
                    name_cell = name_row.find_next_sibling()
                    if name_cell:
                        player_info['real_name'] = name_cell.get_text(strip=True)
                
                # 国家
                country_row = infobox.find('div', string=re.compile(r'Nationality|Country'))
                if country_row:
                    country_cell = country_row.find_next_sibling()
                    if country_cell:
                        player_info['country'] = country_cell.get_text(strip=True)
                
                # 生日
                birth_row = infobox.find('div', string=re.compile(r'Birth|Born'))
                if birth_row:
                    birth_cell = birth_row.find_next_sibling()
                    if birth_cell:
                        player_info['birth_date'] = birth_cell.get_text(strip=True)
                
                # 当前队伍
                team_row = infobox.find('div', string=re.compile(r'Team|Current Team'))
                if team_row:
                    team_cell = team_row.find_next_sibling()
                    if team_cell:
                        player_info['current_team'] = team_cell.get_text(strip=True)
                
                # 位置
                position_row = infobox.find('div', string=re.compile(r'Position|Role'))
                if position_row:
                    position_cell = position_row.find_next_sibling()
                    if position_cell:
                        player_info['position'] = position_cell.get_text(strip=True)
                
                # 总奖金
                earnings_row = infobox.find('div', string=re.compile(r'Approx. Total Winnings'))
                if earnings_row:
                    earnings_cell = earnings_row.find_next_sibling()
                    if earnings_cell:
                        earnings_text = earnings_cell.get_text(strip=True)
                        earnings_match = re.search(r'\$?([\d,]+)', earnings_text)
                        if earnings_match:
                            player_info['total_earnings'] = earnings_match.group(1).replace(',', '')
            
            return player_info
            
        except Exception as e:
            logger.error(f"获取选手信息失败 {player_name}: {e}")
            return None
    
    def search_teams(self, query: str, limit: int = 10) -> List[Dict]:
        """
        搜索战队
        
        Args:
            query: 搜索关键词
            limit: 返回结果数量限制
            
        Returns:
            战队信息列表
        """
        try:
            # 使用Liquipedia的搜索API
            search_params = {
                'action': 'opensearch',
                'search': query,
                'limit': limit,
                'namespace': 0,
                'format': 'json'
            }
            
            response = self._make_request(self.api_url, search_params)
            if not response:
                return []
            
            search_results = response.json()
            if len(search_results) < 2:
                return []
            
            team_names = search_results[1]  # 搜索结果标题列表
            teams = []
            
            for team_name in team_names[:limit]:
                # 过滤掉不是战队的结果
                if any(keyword in team_name.lower() for keyword in ['team', 'gaming', 'esports', 'dota']):
                    team_info = self.get_team_info(team_name)
                    if team_info:
                        teams.append(team_info)
                        
                        # 避免请求过快
                        time.sleep(self.rate_limit_delay)
            
            return teams
            
        except Exception as e:
            logger.error(f"搜索战队失败: {e}")
            return []
    
    def get_recent_tournaments(self, limit: int = 20) -> List[Dict]:
        """
        获取最近的锦标赛列表
        
        Args:
            limit: 返回结果数量限制
            
        Returns:
            锦标赛信息列表
        """
        try:
            # 访问锦标赛列表页面
            tournaments_url = f"{self.base_url}/Dota_2_Tournaments"
            
            response = self._make_request(tournaments_url)
            if not response:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            tournaments = []
            
            # 查找锦标赛表格
            tournament_tables = soup.find_all('table', class_='wikitable')
            
            for table in tournament_tables:
                rows = table.find_all('tr')[1:]  # 跳过表头
                
                for row in rows[:limit]:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 3:
                        tournament_link = cells[0].find('a')
                        if tournament_link:
                            tournament_name = tournament_link.get_text(strip=True)
                            
                            # 基本信息
                            tournament_basic = {
                                'name': tournament_name,
                                'date': cells[1].get_text(strip=True) if len(cells) > 1 else None,
                                'prize_pool': cells[2].get_text(strip=True) if len(cells) > 2 else None,
                                'location': cells[3].get_text(strip=True) if len(cells) > 3 else None
                            }
                            
                            tournaments.append(tournament_basic)
                            
                            if len(tournaments) >= limit:
                                break
                
                if len(tournaments) >= limit:
                    break
            
            return tournaments
            
        except Exception as e:
            logger.error(f"获取最近锦标赛失败: {e}")
            return []
    
    def save_data(self, data: Dict, filename: str, data_dir: str = "data/liquipedia") -> Optional[str]:
        """保存数据到文件"""
        import os
        
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        full_filename = f"{filename}_{timestamp}.json"
        filepath = os.path.join(data_dir, full_filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Liquipedia数据已保存: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"保存Liquipedia数据失败: {e}")
            return None

# 使用示例
if __name__ == "__main__":
    service = LiquipediaService()
    
    # 测试获取战队信息
    print("测试获取战队信息...")
    team_info = service.get_team_info("Team_Spirit")
    if team_info:
        print(f"战队名称: {team_info['name']}")
        print(f"地区: {team_info['region']}")
        print(f"当前阵容: {len(team_info['current_roster'])} 人")
    
    # 测试搜索战队
    print("\n测试搜索战队...")
    teams = service.search_teams("Spirit", limit=3)
    print(f"搜索到 {len(teams)} 个战队")
    
    # 测试获取锦标赛
    print("\n测试获取锦标赛...")
    tournaments = service.get_recent_tournaments(limit=5)
    print(f"获取到 {len(tournaments)} 个锦标赛")
