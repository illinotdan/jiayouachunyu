package main

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/dotabuff/manta"
	"github.com/dotabuff/manta/dota"
)

// ... (所有 struct 定义和 NewDemParser 等函数保持不变) ...
type DemOutput struct {
	MatchInfo    MatchInfo     `json:"matchInfo"`
	Players      []Player      `json:"players"`
	ChatMessages []ChatMessage `json:"chatMessages"`
	CombatLogs   []CombatLog   `json:"combatLogs"`
	Statistics   Statistics    `json:"statistics"`
	SourceFile   string        `json:"sourceFile"`
	ProcessedAt  int64         `json:"processedAt"`
}
type MatchInfo struct {
	GameTime     float32 `json:"gameTime"`
	GameMode     int32   `json:"gameMode"`
	GameModeName string  `json:"gameModeName"`
	MatchID      uint64  `json:"matchId,omitempty"`
	Winner       string  `json:"winner,omitempty"`
	Duration     float32 `json:"duration"`
}
type Player struct {
	PlayerID   int32  `json:"playerId"`
	PlayerName string `json:"playerName,omitempty"`
	HeroName   string `json:"heroName,omitempty"`
	SteamID    uint64 `json:"steamId,omitempty"`
	Team       int32  `json:"team"`
}
type ChatMessage struct {
	Tick       uint32  `json:"tick"`
	GameTime   float32 `json:"gameTime,omitempty"`
	PlayerName string  `json:"playerName,omitempty"`
	Message    string  `json:"message,omitempty"`
}
type CombatLog struct {
	Tick       uint32  `json:"tick"`
	GameTime   float32 `json:"gameTime,omitempty"`
	Type       string  `json:"type"`
	SourceName string  `json:"sourceName,omitempty"`
	TargetName string  `json:"targetName,omitempty"`
	Value      uint32  `json:"value,omitempty"`
}
type Statistics struct {
	TotalTicks       uint32  `json:"totalTicks"`
	Duration         float32 `json:"duration"`
	CombatLogCount   int     `json:"combatLogCount"`
	ChatMessageCount int     `json:"chatMessageCount"`
}
type DemParser struct {
	parser    *manta.Parser
	output    *DemOutput
	playerMap map[int32]*Player
	gameTime  float32
}

func NewDemParser() *DemParser {
	return &DemParser{
		output: &DemOutput{
			Players:      make([]Player, 0),
			ChatMessages: make([]ChatMessage, 0),
			CombatLogs:   make([]CombatLog, 0),
			ProcessedAt:  time.Now().Unix(),
		},
		playerMap: make(map[int32]*Player),
	}
}

func (dp *DemParser) Parse(filename string) error {
	dp.output.SourceFile = filepath.Base(filename)
	f, err := os.Open(filename)
	if err != nil {
		return fmt.Errorf("unable to open file: %v", err)
	}
	defer f.Close()

	parser, err := manta.NewStreamParser(f)
	if err != nil {
		return fmt.Errorf("unable to create parser: %v", err)
	}
	dp.parser = parser

	dp.registerCallbacks()

	fmt.Println("Starting parse...")
	startTime := time.Now()

	// 增加 panic recovery 来捕获任何意外的运行时错误
	defer func() {
		if r := recover(); r != nil {
			fmt.Printf("Recovered from a panic during parsing: %v\n", r)
			fmt.Println("Parsing will stop, but collected data will be saved.")
		}
	}()

	err = parser.Start()
	if err != nil {
		// manta 正常结束时也可能返回一个 error，比如 io.EOF，这不一定是问题
		fmt.Printf("Parser stopped with message: %v\n", err)
	}

	duration := time.Since(startTime)
	fmt.Printf("Parsing process finished in %.2f seconds\n", duration.Seconds())

	dp.finalize()
	return nil
}

// ==========================================================
// ## 核心逻辑: 注册回调函数 (增加安全检查) ##
// ==========================================================
func (dp *DemParser) registerCallbacks() {
	p := dp.parser

	p.Callbacks.OnCUserMessageSayText2(func(m *dota.CUserMessageSayText2) error {
		chat := ChatMessage{
			Tick:       p.Tick,
			GameTime:   dp.gameTime,
			PlayerName: m.GetParam1(),
			Message:    m.GetParam2(),
		}
		dp.output.ChatMessages = append(dp.output.ChatMessages, chat)
		return nil
	})

	p.Callbacks.OnCMsgDOTACombatLogEntry(func(m *dota.CMsgDOTACombatLogEntry) error {
		// 安全检查: 确保 parser 实例不为 nil
		if p == nil {
			return nil
		}
		sourceName, _ := p.LookupStringByIndex("CombatLogNames", int32(m.GetAttackerName()))
		targetName, _ := p.LookupStringByIndex("CombatLogNames", int32(m.GetTargetName()))

		log := CombatLog{
			Tick:       p.Tick,
			GameTime:   dp.gameTime,
			Type:       getCombatLogTypeName(m.GetType()),
			SourceName: sourceName,
			TargetName: targetName,
			Value:      m.GetValue(),
		}
		dp.output.CombatLogs = append(dp.output.CombatLogs, log)
		return nil
	})

	p.Callbacks.OnCSVCMsg_PacketEntities(func(m *dota.CSVCMsg_PacketEntities) error {
		// 安全检查: 确保 parser 实例不为 nil
		if p == nil {
			return nil
		}

		// 查找游戏规则实体
		gameRulesEntities := p.FilterEntity(func(e *manta.Entity) bool {
			// 增加对 nil 实体的检查
			return e != nil && e.GetClassName() == "CDOTAGamerulesProxy"
		})

		// 关键安全检查: 确保我们真的找到了实体
		if len(gameRulesEntities) > 0 {
			gameRules := gameRulesEntities[0]
			if gameTime, ok := gameRules.GetFloat32("m_pGameRules.m_flGameTime"); ok {
				dp.gameTime = gameTime
			}
			if gameMode, ok := gameRules.GetInt32("m_pGameRules.m_iGameMode"); ok {
				dp.output.MatchInfo.GameMode = gameMode
			}
			if matchID, ok := gameRules.GetUint64("m_pGameRules.m_unMatchID"); ok {
				dp.output.MatchInfo.MatchID = matchID
			}
		}

		// 查找玩家资源实体
		playerResourceEntities := p.FilterEntity(func(e *manta.Entity) bool {
			return e != nil && e.GetClassName() == "CDOTA_PlayerResource"
		})
		
		// 关键安全检查: 确保我们真的找到了实体
		if len(playerResourceEntities) > 0 {
			playerResource := playerResourceEntities[0]
			for i := 0; i < 24; i++ {
				prefix := fmt.Sprintf("m_vecPlayerData.%04d", i)
				playerName, okName := playerResource.GetString(prefix + ".m_iszPlayerName")

				if okName && playerName != "" {
					playerID := int32(i)
					if _, exists := dp.playerMap[playerID]; !exists {
						heroID32, _ := playerResource.GetInt32(fmt.Sprintf("m_vecPlayerTeamData.%04d.m_nSelectedHeroID", i))
						heroEntity := p.FindEntity(heroID32)
						heroName := "Unknown"
						if heroEntity != nil {
							heroName = strings.Replace(heroEntity.GetClassName(), "CDOTA_Unit_Hero_", "", 1)
						}

						steamID, _ := playerResource.GetUint64(prefix + ".m_iPlayerSteamID")
						teamVal, _ := playerResource.GetInt32(prefix + ".m_iPlayerTeam")

						dp.playerMap[playerID] = &Player{
							PlayerID:   playerID,
							PlayerName: playerName,
							SteamID:    steamID,
							HeroName:   heroName,
							Team:       teamVal,
						}
					}
				}
			}
		}
		return nil
	})

	p.Callbacks.OnCDemoFileInfo(func(m *dota.CDemoFileInfo) error {
		if m != nil {
			dp.output.MatchInfo.Duration = m.GetPlaybackTime()
		}
		return nil
	})
}

// ... (finalize, SaveJSON, main 和辅助函数保持不变) ...
func (dp *DemParser) finalize() {
	for _, player := range dp.playerMap {
		dp.output.Players = append(dp.output.Players, *player)
	}
	if dp.parser != nil {
		dp.output.Statistics.TotalTicks = dp.parser.Tick
	}
	dp.output.Statistics.Duration = dp.gameTime
	dp.output.Statistics.ChatMessageCount = len(dp.output.ChatMessages)
	dp.output.Statistics.CombatLogCount = len(dp.output.CombatLogs)
	dp.output.MatchInfo.GameModeName = getGameModeName(dp.output.MatchInfo.GameMode)
	dp.output.MatchInfo.GameTime = dp.gameTime
}

func (dp *DemParser) SaveJSON(outputPath string) error {
	jsonData, err := json.MarshalIndent(dp.output, "", "  ")
	if err != nil {
		return fmt.Errorf("error marshaling JSON: %v", err)
	}
	err = os.WriteFile(outputPath, jsonData, 0644)
	if err != nil {
		return fmt.Errorf("error writing file: %v", err)
	}
	fmt.Printf("JSON saved to: %s (%.2f KB)\n",
		outputPath,
		float64(len(jsonData))/1024)
	return nil
}

func main() {
	if len(os.Args) < 2 {
		fmt.Println("Usage: go run main.go <input.dem>")
		os.Exit(1)
	}
	inputPath := os.Args[1]
	outputPath := strings.Replace(inputPath, ".dem", "_parsed_go.json", 1)

	fmt.Println("========================================")
	fmt.Println("Go Manta DEM to JSON Converter")
	fmt.Println("========================================")

	parser := NewDemParser()
	err := parser.Parse(inputPath)
	if err != nil {
		log.Printf("Error during parsing: %v\n", err)
	}

	err = parser.SaveJSON(outputPath)
	if err != nil {
		log.Fatalf("Error saving JSON: %v", err)
	}

	fmt.Println("========================================")
	fmt.Printf("Conversion completed!\n")
	fmt.Printf("Players found: %d\n", len(parser.output.Players))
	fmt.Printf("Chat messages found: %d\n", len(parser.output.ChatMessages))
	fmt.Printf("Combat logs found: %d\n", len(parser.output.CombatLogs))
	fmt.Println("========================================")
}

func getCombatLogTypeName(logType dota.DOTA_COMBATLOG_TYPES) string {
	// 增加对无效 logType 的安全检查
	if _, ok := dota.DOTA_COMBATLOG_TYPES_name[int32(logType)]; ok {
		return dota.DOTA_COMBATLOG_TYPES_name[int32(logType)]
	}
	return "UNKNOWN"
}

func getGameModeName(mode int32) string {
	modes := map[int32]string{
		0: "NONE", 1: "ALL_PICK", 2: "CAPTAINS_MODE", 3: "RANDOM_DRAFT",
		4: "SINGLE_DRAFT", 5: "ALL_RANDOM", 22: "RANKED_ALL_PICK", 23: "TURBO",
	}
	if name, ok := modes[mode]; ok {
		return name
	}
	return fmt.Sprintf("UNKNOWN_%d", mode)
}