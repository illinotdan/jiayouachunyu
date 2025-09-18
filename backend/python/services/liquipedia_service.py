"""
Liquipedia数据获取服务 - 优化集成版
生产环境版本 - 专业的Dota2数据抓取服务
保持原有业务逻辑不变，优化集成接口
"""

import time
import json
import re
from datetime import datetime
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
import logging

from playwright.sync_api import sync_playwright, Browser as SyncBrowser, BrowserContext as SyncBrowserContext, Page as SyncPage

logger = logging.getLogger(__name__)


class LiquipediaService:
    """Liquipedia数据获取服务 - 集成优化版"""

    def __init__(self,
                 rate_limit_delay: float = 2.0,
                 headless: bool = True,
                 debug: bool = False,
                 timeout: int = 60000):
        """
        初始化Liquipedia服务

        Args:
            rate_limit_delay: 请求间隔（秒）
            headless: 是否无头模式
            debug: 是否开启调试模式
            timeout: 页面加载超时时间（毫秒）
        """
        self.base_url = "https://liquipedia.net/dota2"
        self.api_url = "https://liquipedia.net/dota2/api.php"
        self.rate_limit_delay = rate_limit_delay
        self.headless = headless
        self.debug = debug
        self.timeout = timeout

        # Playwright实例
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

        # 统计信息
        self.stats = {
            'requests_made': 0,
            'successful_requests': 0,
            'failed_requests': 0,
        }

        # 连接状态跟踪 - 新增，用于集成
        self._connection_status = 'unknown'
        self._last_successful_request = None

    def _setup_browser(self):
        """初始化浏览器"""
        try:
            self.playwright = sync_playwright().start()

            # 浏览器启动参数
            browser_args = [
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--no-first-run',
                '--disable-default-apps',
                '--disable-translate',
                '--disable-sync',
                '--no-report-upload',
            ]

            self.browser = self.playwright.chromium.launch(
                headless=self.headless,
                args=browser_args
            )

            # 浏览器上下文配置
            self.context = self.browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1366, 'height': 768},
                locale='en-US',
                extra_http_headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
            )

            self.page = self.context.new_page()
            self.page.set_default_timeout(self.timeout)

            # 反检测脚本
            self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
                window.chrome = { runtime: {} };
            """)

            if self.debug:
                logger.info("浏览器初始化成功")

            self._connection_status = 'ready'

        except Exception as e:
            logger.error(f"浏览器初始化失败: {e}")
            self._connection_status = 'failed'
            self._cleanup()
            raise

    def _cleanup(self):
        """清理资源"""
        try:
            if self.page: self.page.close()
            if self.context: self.context.close()
            if self.browser: self.browser.close()
            if self.playwright: self.playwright.stop()

            if self.debug:
                logger.info("浏览器资源清理完成")
        except Exception as e:
            if self.debug:
                logger.error(f"清理资源时出错: {e}")

    def _navigate_to_page(self, url: str, params: Optional[Dict] = None, max_retries: int = 3) -> Optional[str]:
        """导航到页面并获取内容"""
        for attempt in range(max_retries):
            try:
                if not self.browser:
                    self._setup_browser()

                # 构建URL
                if params:
                    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
                    full_url = f"{url}?{query_string}"
                else:
                    full_url = url

                if self.debug:
                    logger.info(f"访问页面 (尝试 {attempt + 1}/{max_retries}): {full_url}")

                # 请求间隔
                if attempt > 0:
                    time.sleep(2 ** attempt)

                # 访问页面
                response = self.page.goto(full_url, wait_until='domcontentloaded', timeout=self.timeout)

                if not response or response.status >= 400:
                    if self.debug:
                        logger.warning(f"页面响应异常: {response.status if response else 'None'}")
                    continue

                # 等待加载
                try:
                    self.page.wait_for_load_state('networkidle', timeout=30000)
                except:
                    if self.debug:
                        logger.warning("等待网络空闲超时")

                time.sleep(1)  # 额外等待

                content = self.page.content()

                if len(content) < 100:
                    if self.debug:
                        logger.warning(f"页面内容过短: {len(content)} 字符")
                    continue

                self.stats['requests_made'] += 1
                self.stats['successful_requests'] += 1
                self._last_successful_request = datetime.now()
                self._connection_status = 'healthy'
                
                time.sleep(self.rate_limit_delay)

                return content

            except Exception as e:
                if self.debug:
                    logger.error(f"页面访问失败 (尝试 {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    self.stats['failed_requests'] += 1
                    self._connection_status = 'error'
                    return None

        return None

    # ========== 统一服务接口 - 新增 ==========
    
    def test_connection(self) -> bool:
        """测试连接 - 统一接口"""
        try:
            # 尝试获取一个简单的页面来测试连接
            test_content = self._navigate_to_page(f"{self.base_url}/Main_Page")
            success = test_content is not None and len(test_content) > 1000
            
            if success:
                self._connection_status = 'healthy'
                logger.info("Liquipedia 连接测试成功")
            else:
                self._connection_status = 'failed'
                logger.warning("Liquipedia 连接测试失败")
            
            return success
        except Exception as e:
            logger.error(f"Liquipedia 连接测试异常: {e}")
            self._connection_status = 'error'
            return False
    
    def get_service_status(self) -> Dict:
        """获取服务状态 - 统一接口"""
        return {
            'service_name': 'Liquipedia',
            'available': self._connection_status == 'healthy',
            'connection_status': self._connection_status,
            'browser_ready': self.browser is not None,
            'last_successful_request': self._last_successful_request.isoformat() if self._last_successful_request else None,
            'rate_limit_delay': self.rate_limit_delay,
            'stats': self.stats.copy(),
            'base_url': self.base_url,
            'timestamp': datetime.utcnow().isoformat()
        }

    # ========== 原有业务逻辑保持不变 ==========

    def get_team_info(self, team_name: str) -> Optional[Dict]:
        """
        获取战队详细信息 - 保持原有逻辑不变

        Args:
            team_name: 战队名称

        Returns:
            战队信息字典或None
        """
        try:
            team_url = f"{self.base_url}/{team_name.replace(' ', '_')}"

            if self.debug:
                logger.info(f"获取战队信息: {team_name}")

            content = self._navigate_to_page(team_url)
            if not content:
                return None

            soup = BeautifulSoup(content, 'html.parser')

            team_info = {
                'name': team_name,
                'url': team_url,
                'logo_url': None,
                'region': None,
                'founded_date': None,
                'total_earnings': None,
                'current_roster': [],
                'achievements': [],
            }

            # 提取Logo
            logo_selectors = [
                'div.infobox-image img',
                'div.floatright img',
                'img[alt*="logo" i]',
                '.teamcard img'
            ]

            for selector in logo_selectors:
                logo_img = soup.select_one(selector)
                if logo_img and logo_img.get('src'):
                    src = logo_img['src']
                    if src.startswith('//'):
                        team_info['logo_url'] = f"https:{src}"
                    elif src.startswith('/'):
                        team_info['logo_url'] = f"https://liquipedia.net{src}"
                    else:
                        team_info['logo_url'] = src
                    break

            # 获取信息框
            infobox = soup.select_one('div.fo-nttax-infobox') or soup.select_one('div.infobox') or soup.select_one('table.infobox')

            if infobox:
                # 提取基本信息
                self._extract_team_basic_info(infobox, team_info)

                # 提取总奖金 - 增强版
                self._extract_team_earnings(soup, team_info)

            # 提取阵容
            self._extract_team_roster(soup, team_info)

            # 提取主要成就
            self._extract_team_achievements(soup, team_info)

            return team_info

        except Exception as e:
            if self.debug:
                logger.error(f"解析战队 '{team_name}' 失败: {e}")
            return None

    def _extract_team_basic_info(self, infobox: BeautifulSoup, team_info: Dict):
        """提取战队基本信息"""
        info_patterns = {
            'region': [r'Region', r'Location', r'Country'],
            'founded_date': [r'Created', r'Founded', r'Formed', r'Established']
        }

        for key, patterns in info_patterns.items():
            for pattern in patterns:
                for element in infobox.find_all(string=re.compile(pattern, re.IGNORECASE)):
                    parent = element.parent
                    if parent:
                        next_element = parent.find_next_sibling()
                        if next_element:
                            text = next_element.get_text(strip=True)
                            if text and len(text) < 100:
                                team_info[key] = text
                                break
                if team_info[key]:
                    break

    def _extract_team_earnings(self, soup: BeautifulSoup, team_info: Dict):
        """增强的总奖金提取"""
        # 策略1: 从信息框提取
        earnings_patterns = [r'Total Winnings', r'Prize Money', r'Earnings', r'Total Earnings', r'Winnings']

        infobox = soup.select_one('div.fo-nttax-infobox') or soup.select_one('div.infobox')
        if infobox:
            for pattern in earnings_patterns:
                for element in infobox.find_all(string=re.compile(pattern, re.IGNORECASE)):
                    parent = element.parent
                    if parent:
                        next_element = parent.find_next_sibling()
                        if next_element:
                            earnings_text = next_element.get_text(strip=True)
                            amount = self._parse_money_amount(earnings_text)
                            if amount:
                                team_info['total_earnings'] = amount
                                return

        # 策略2: 查找专门的奖金区域
        earnings_selectors = [
            'div.earnings',
            'span.earnings',
            '[class*="earning" i]',
            '[class*="prize" i]',
            '[class*="winnings" i]'
        ]

        for selector in earnings_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                amount = self._parse_money_amount(text)
                if amount:
                    team_info['total_earnings'] = amount
                    return

        # 策略3: 查找包含美元符号的文本
        all_text_elements = soup.find_all(string=re.compile(r'\$[\d,]+'))
        for text in all_text_elements:
            if any(keyword in text.lower() for keyword in ['total', 'earning', 'winning', 'prize']):
                amount = self._parse_money_amount(text)
                if amount and int(amount.replace(',', '')) > 1000:  # 过滤小额奖金
                    team_info['total_earnings'] = amount
                    return

    def _parse_money_amount(self, text: str) -> Optional[str]:
        """解析金额文本"""
        # 匹配各种金额格式
        money_patterns = [
            r'\$\s*([\d,]+(?:\.\d{2})?)',  # $1,234,567.89
            r'USD\s*([\d,]+(?:\.\d{2})?)',  # USD 1,234,567
            r'([\d,]+(?:\.\d{2})?)\s*USD',  # 1,234,567 USD
            r'\$?\s*([\d,]+(?:\.\d{2})?)'   # 通用数字格式
        ]

        for pattern in money_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount = match.group(1).replace(' ', '')
                # 验证是否为合理的金额
                try:
                    numeric_amount = float(amount.replace(',', ''))
                    if numeric_amount >= 100:  # 至少100美元
                        return amount
                except:
                    continue
        return None

    def _extract_team_roster(self, soup: BeautifulSoup, team_info: Dict):
        """提取战队阵容"""
        roster_patterns = [
            r'Active_Roster', r'Current_Roster', r'Roster', r'Squad', r'Players'
        ]

        for pattern in roster_patterns:
            roster_section = soup.find('span', {'id': re.compile(pattern, re.I)})
            if not roster_section:
                roster_section = soup.find(string=re.compile(pattern, re.I))
                if roster_section:
                    roster_section = roster_section.find_parent()

            if roster_section:
                roster_table = roster_section.find_next('table')
                if not roster_table:
                    roster_table = roster_section.find_parent().find_next('table')

                if roster_table and roster_table.find('tr'):
                    rows = roster_table.find_all('tr')[1:]  # 跳过表头
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 1:
                            player_id = cells[0].get_text(strip=True)

                            # 提取选手真实姓名 - 修复格式问题
                            player_name = self._extract_player_name(cells)

                            if player_id and player_id not in ['', '-', 'N/A']:
                                team_info['current_roster'].append({
                                    'id': player_id,
                                    'name': player_name,
                                })
                    break

    def _extract_player_name(self, cells: List) -> str:
        """提取并清理选手姓名"""
        if len(cells) <= 1:
            return ""

        # 检查第二列及后续列
        for i in range(1, min(len(cells), 4)):
            text = cells[i].get_text(strip=True)
            if not text:
                continue

            # 跳过位置信息
            if text.lower() in ['carry', 'mid', 'midlane', 'offlane', 'offlaner', 'support', 'captain', 'coach']:
                continue

            # 处理括号中的姓名格式
            # 修复 "(Name)Name" 格式问题
            if '(' in text and ')' in text:
                # 提取括号内容
                bracket_match = re.search(r'\(([^)]+)\)', text)
                if bracket_match:
                    bracket_content = bracket_match.group(1).strip()
                    # 移除括号及其内容，获取剩余部分
                    remaining = re.sub(r'\([^)]+\)', '', text).strip()

                    # 如果括号内外内容相同，只保留一个
                    if bracket_content == remaining:
                        return bracket_content
                    # 如果有意义的内容，优先选择较长的
                    elif len(bracket_content) > len(remaining) and len(bracket_content) > 2:
                        return bracket_content
                    elif len(remaining) > 2:
                        return remaining

            # 如果没有括号问题，直接返回
            if len(text) > 2:
                return text

        return ""

    def _extract_team_achievements(self, soup: BeautifulSoup, team_info: Dict):
        """提取战队主要成就"""
        achievements = []

        # 查找成就相关的区域
        achievement_sections = soup.find_all(['span', 'h2', 'h3'],
                                           string=re.compile(r'Achievement|Award|Notable|Major', re.I))

        for section in achievement_sections[:3]:  # 最多查看3个区域
            # 查找该区域后的列表或表格
            next_element = section.find_next(['ul', 'ol', 'table'])
            if next_element:
                if next_element.name in ['ul', 'ol']:
                    items = next_element.find_all('li')[:5]  # 最多5个成就
                    for item in items:
                        text = item.get_text(strip=True)
                        if len(text) > 10 and len(text) < 200:
                            achievements.append(text)
                elif next_element.name == 'table':
                    rows = next_element.find_all('tr')[1:6]  # 最多5行
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if cells:
                            text = ' - '.join([cell.get_text(strip=True) for cell in cells[:2]])
                            if len(text) > 10:
                                achievements.append(text)

        team_info['achievements'] = achievements[:5]  # 最多保留5个主要成就

    def search_teams(self, query: str, limit: int = 10) -> List[Dict]:
        """
        搜索战队 - 保持原有逻辑不变

        Args:
            query: 搜索关键词
            limit: 结果数量限制

        Returns:
            搜索结果列表
        """
        try:
            if self.debug:
                logger.info(f"搜索战队: {query}")

            # API搜索
            search_params = {
                'action': 'opensearch',
                'search': query,
                'limit': str(limit),
                'namespace': '0',
                'format': 'json'
            }

            content = self._navigate_to_page(self.api_url, search_params)
            if not content:
                return []

            # 处理API响应
            try:
                if '<pre>' in content and '</pre>' in content:
                    json_match = re.search(r'<pre[^>]*>(.*?)</pre>', content, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(1).strip()
                        search_results = json.loads(json_str)
                        if len(search_results) >= 2 and search_results[1]:
                            return [{'name': name} for name in search_results[1][:limit]]
                else:
                    search_results = json.loads(content)
                    if len(search_results) >= 2 and search_results[1]:
                        return [{'name': name} for name in search_results[1][:limit]]
            except json.JSONDecodeError:
                if self.debug:
                    logger.info("API搜索失败，尝试备用方法")
                return self._fallback_search(query, limit)

            return []

        except Exception as e:
            if self.debug:
                logger.error(f"搜索失败: {e}")
            return []

    def _fallback_search(self, query: str, limit: int = 10) -> List[Dict]:
        """备用搜索方法"""
        try:
            search_url = f"{self.base_url}/Special:Search"
            search_params = {'search': query}

            content = self._navigate_to_page(search_url, search_params)
            if not content:
                return []

            soup = BeautifulSoup(content, 'html.parser')
            results = []

            # 查找搜索结果
            search_results = soup.find_all('div', class_='mw-search-result-heading')
            if not search_results:
                search_results = soup.find_all('a', href=re.compile(r'/dota2/[^/]+$'))

            for result in search_results[:limit]:
                if hasattr(result, 'find'):
                    link = result.find('a')
                    if link:
                        team_name = link.get_text(strip=True)
                        if team_name and len(team_name) > 1:
                            results.append({'name': team_name})
                elif result.get('href'):
                    team_name = result.get_text(strip=True)
                    if team_name and len(team_name) > 1:
                        results.append({'name': team_name})

            return results

        except Exception as e:
            if self.debug:
                logger.error(f"备用搜索失败: {e}")
            return []

    def get_tournaments(self, limit: int = 20, tournament_type: str = 'recent') -> List[Dict]:
        """
        获取锦标赛列表 - 保持原有逻辑不变

        Args:
            limit: 结果数量限制
            tournament_type: 锦标赛类型 ('recent', 'ongoing', 'completed')

        Returns:
            锦标赛信息列表
        """
        try:
            if self.debug:
                logger.info(f"获取锦标赛列表: {tournament_type}")

            # 根据类型选择URL
            if tournament_type == 'ongoing':
                urls = [f"{self.base_url}/Ongoing_Tournaments", f"{self.base_url}/Portal:Tournaments"]
            elif tournament_type == 'completed':
                urls = [f"{self.base_url}/Completed_Tournaments", f"{self.base_url}/Portal:Tournaments"]
            else:
                urls = [f"{self.base_url}/Portal:Tournaments", f"{self.base_url}/Recent_and_Ongoing_Tournaments"]

            for url in urls:
                content = self._navigate_to_page(url)
                if not content:
                    continue

                soup = BeautifulSoup(content, 'html.parser')

                # 尝试多种提取策略
                tournaments = (
                    self._extract_tournaments_from_tables(soup, limit) or
                    self._extract_tournaments_from_sections(soup, limit) or
                    self._extract_tournaments_from_links(soup, limit)
                )

                if tournaments:
                    return tournaments

            return []

        except Exception as e:
            if self.debug:
                logger.error(f"获取锦标赛失败: {e}")
            return []

    def _extract_tournaments_from_tables(self, soup: BeautifulSoup, limit: int) -> List[Dict]:
        """从表格中提取锦标赛"""
        tournaments = []
        tables = soup.find_all('table', class_=['wikitable', 'sortable'])

        for table in tables:
            # 检查表格是否包含锦标赛数据
            if not self._is_tournament_table(table):
                continue

            rows = table.find_all('tr')[1:]  # 跳过表头

            for row in rows:
                if len(tournaments) >= limit:
                    break

                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    name_cell = cells[0]
                    name_link = name_cell.find('a')
                    tournament_name = name_link.get_text(strip=True) if name_link else name_cell.get_text(strip=True)

                    if self._is_valid_tournament_name(tournament_name):
                        tournaments.append({
                            'name': tournament_name,
                            'date': cells[1].get_text(strip=True) if len(cells) > 1 else '',
                            'prize_pool': cells[2].get_text(strip=True) if len(cells) > 2 else '',
                            'status': self._determine_tournament_status(cells),
                        })

            if tournaments:
                break

        return tournaments

    def _extract_tournaments_from_sections(self, soup: BeautifulSoup, limit: int) -> List[Dict]:
        """从特定区域提取锦标赛"""
        tournaments = []
        sections = soup.find_all(['div', 'section'], class_=re.compile(r'tournament|competition|event', re.I))

        for section in sections:
            links = section.find_all('a', href=re.compile(r'/dota2/[^/]+'))

            for link in links[:limit]:
                tournament_name = link.get_text(strip=True)
                if self._is_valid_tournament_name(tournament_name):
                    # 尝试获取日期信息
                    date_info = self._extract_date_from_context(link)

                    tournaments.append({
                        'name': tournament_name,
                        'date': date_info,
                        'prize_pool': '',
                        'status': 'unknown',
                    })

                if len(tournaments) >= limit:
                    break

        return tournaments

    def _extract_tournaments_from_links(self, soup: BeautifulSoup, limit: int) -> List[Dict]:
        """从链接中提取锦标赛"""
        tournaments = []
        all_links = soup.find_all('a', href=re.compile(r'/dota2/[^/]+'))

        tournament_keywords = [
            'tournament', 'championship', 'cup', 'league', 'major', 'minor',
            'open', 'series', 'invitational', 'masters', 'pro', 'circuit',
            '2024', '2025'
        ]

        for link in all_links:
            tournament_name = link.get_text(strip=True)

            if (self._is_valid_tournament_name(tournament_name) and
                any(keyword in tournament_name.lower() for keyword in tournament_keywords)):

                # 避免重复
                if not any(t['name'] == tournament_name for t in tournaments):
                    tournaments.append({
                        'name': tournament_name,
                        'date': '',
                        'prize_pool': '',
                        'status': 'unknown',
                        'url': f"https://liquipedia.net{link.get('href', '')}"
                    })

                if len(tournaments) >= limit:
                    break

        return tournaments

    def _is_tournament_table(self, table: BeautifulSoup) -> bool:
        """判断表格是否为锦标赛表格"""
        table_text = table.get_text().lower()
        tournament_indicators = ['tournament', 'competition', 'championship', 'prize', 'date', '2024', '2025']
        return any(indicator in table_text for indicator in tournament_indicators)

    def _is_valid_tournament_name(self, name: str) -> bool:
        """验证锦标赛名称是否有效"""
        if not name or len(name) < 3 or len(name) > 100:
            return False

        invalid_patterns = [
            r'^tier \d+$',
            r'^[a-z]+:',  # 命名空间前缀
            r'^\d+$',     # 纯数字
        ]

        return not any(re.match(pattern, name.lower()) for pattern in invalid_patterns)

    def _determine_tournament_status(self, cells: List) -> str:
        """确定锦标赛状态"""
        for cell in cells:
            text = cell.get_text().lower()
            if 'ongoing' in text or 'live' in text:
                return 'ongoing'
            elif 'completed' in text or 'finished' in text:
                return 'completed'
            elif 'upcoming' in text or 'scheduled' in text:
                return 'upcoming'
        return 'unknown'

    def _extract_date_from_context(self, link: BeautifulSoup) -> str:
        """从上下文中提取日期"""
        parent = link.find_parent(['td', 'div', 'li'])
        if parent:
            date_match = re.search(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\w+ \d{1,2}, \d{4})', parent.get_text())
            if date_match:
                return date_match.group(1)
        return ''

    def get_stats(self) -> Dict:
        """获取服务统计信息"""
        return self.stats.copy()
    
    # ========== 新增批量处理方法，保持与其他服务接口一致 ==========
    
    def batch_collect_teams(self, team_names: List[str], save_results: bool = False) -> Dict:
        """
        批量收集战队数据
        
        Args:
            team_names: 战队名称列表
            save_results: 是否保存结果
        """
        results = {
            'batch_id': datetime.now().strftime("%Y%m%d_%H%M%S"),
            'total_teams': len(team_names),
            'completed_teams': 0,
            'failed_teams': 0,
            'results': {},
            'errors': []
        }
        
        for i, team_name in enumerate(team_names):
            logger.info(f"处理战队 {i+1}/{len(team_names)}: {team_name}")
            
            try:
                team_data = self.get_team_info(team_name)
                
                if team_data:
                    results['results'][team_name] = {
                        'success': True,
                        'data': team_data,
                        'roster_count': len(team_data.get('current_roster', [])),
                        'has_earnings': bool(team_data.get('total_earnings'))
                    }
                    results['completed_teams'] += 1
                else:
                    results['results'][team_name] = {
                        'success': False,
                        'data': None,
                        'error': '无法获取战队数据'
                    }
                    results['failed_teams'] += 1
                    results['errors'].append(f"Team {team_name}: 无法获取数据")
                
                # 保存数据（如果指定）
                if save_results and team_data:
                    self._save_team_data(team_data, team_name)
                
                # 控制请求频率
                time.sleep(self.rate_limit_delay)
                
            except Exception as e:
                logger.error(f"处理战队 {team_name} 失败: {e}")
                results['failed_teams'] += 1
                results['errors'].append(f"Team {team_name}: {str(e)}")
        
        # 生成批处理报告
        results['success_rate'] = results['completed_teams'] / results['total_teams'] if results['total_teams'] > 0 else 0
        results['summary'] = f"完成 {results['completed_teams']}/{results['total_teams']} 个战队"
        
        logger.info(f"批量收集完成: {results['summary']}")
        return results
    
    def _save_team_data(self, team_data: Dict, team_name: str) -> Optional[str]:
        """保存战队数据到文件"""
        try:
            import os
            
            data_dir = "data/liquipedia_teams"
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"team_{team_name.replace(' ', '_')}_{timestamp}.json"
            filepath = os.path.join(data_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(team_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"战队数据已保存: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"保存战队数据失败: {e}")
            return None

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self._cleanup()


# 使用示例
def main():
    """主程序示例"""
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 使用服务
    with LiquipediaService(headless=True, debug=True) as service:
        # 测试连接
        logger.info("测试Liquipedia连接...")
        if service.test_connection():
            logger.info("✅ Liquipedia 连接成功")
            
            # 获取服务状态
            status = service.get_service_status()
            logger.info(f"服务状态: {status['connection_status']}")
        else:
            logger.warning("❌ Liquipedia 连接失败")
            return
        
        # 获取战队信息
        logger.info("获取Team Spirit信息...")
        team_info = service.get_team_info("Team Spirit")
        if team_info:
            logger.info(f"战队: {team_info['name']}")
            logger.info(f"地区: {team_info['region']}")
            logger.info(f"成立: {team_info['founded_date']}")
            logger.info(f"奖金: ${team_info['total_earnings']}" if team_info['total_earnings'] else "奖金: 未找到")
            logger.info(f"阵容: {len(team_info['current_roster'])} 人")
            for player in team_info['current_roster']:
                name_part = f" ({player['name']})" if player['name'] else ""
                logger.info(f"  - {player['id']}{name_part}")

        logger.info("\n" + "="*50)

        # 搜索战队
        logger.info("搜索'OG'...")
        teams = service.search_teams("OG", limit=5)
        for i, team in enumerate(teams, 1):
            logger.info(f"{i}. {team['name']}")

        logger.info("\n" + "="*50)

        # 获取锦标赛
        logger.info("获取最近锦标赛...")
        tournaments = service.get_tournaments(limit=10)
        for i, tournament in enumerate(tournaments, 1):
            logger.info(f"{i}. {tournament['name']}")
            if tournament['date']:
                logger.info(f"   日期: {tournament['date']}")

        # 显示统计
        stats = service.get_stats()
        logger.info(f"\n统计: 成功 {stats['successful_requests']}/{stats['requests_made']}")


if __name__ == "__main__":
    main()