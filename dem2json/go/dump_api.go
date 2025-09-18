package main

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
	"reflect"
	"sort"
	"strings"

	"github.com/dotabuff/manta"
	"github.com/dotabuff/manta/dota"
)

// API信息结构
type APIInfo struct {
	ParserInfo     TypeInfo            `json:"parser"`
	CallbacksInfo  TypeInfo            `json:"callbacks"`
	EntityInfo     TypeInfo            `json:"entity"`
	GameEventInfo  TypeInfo            `json:"gameEvent"`
	DotaConstants  map[string]int      `json:"dotaConstants"`
	SampleData     SampleData          `json:"sampleData"`
}

type TypeInfo struct {
	Fields  []FieldInfo  `json:"fields"`
	Methods []MethodInfo `json:"methods"`
}

type FieldInfo struct {
	Name string `json:"name"`
	Type string `json:"type"`
}

type MethodInfo struct {
	Name       string   `json:"name"`
	Parameters []string `json:"parameters"`
	Returns    []string `json:"returns"`
	Signature  string   `json:"signature"`
}

type SampleData struct {
	EntityClasses    []string          `json:"entityClasses"`
	EntityProperties map[string][]string `json:"entityProperties"`
	GameEvents       []string          `json:"gameEvents"`
}

func main() {
	if len(os.Args) < 2 {
		fmt.Println("Usage: go run dump_api.go <sample.dem>")
		os.Exit(1)
	}

	file, err := os.Open(os.Args[1])
	if err != nil {
		log.Fatalf("无法打开文件: %v", err)
	}
	defer file.Close()

	parser, err := manta.NewStreamParser(file)
	if err != nil {
		log.Fatalf("无法创建 parser: %v", err)
	}

	fmt.Println("========================================")
	fmt.Println("Manta API 完整导出")
	fmt.Println("========================================\n")

	apiInfo := APIInfo{
		DotaConstants: make(map[string]int),
		SampleData: SampleData{
			EntityClasses:    []string{},
			EntityProperties: make(map[string][]string),
			GameEvents:       []string{},
		},
	}

	// 1. 分析 Parser 类型
	fmt.Println("分析 Parser 类型...")
	apiInfo.ParserInfo = analyzeType(reflect.TypeOf(parser).Elem(), reflect.TypeOf(parser))

	// 2. 分析 Callbacks
	fmt.Println("分析 Callbacks 类型...")
	if parser.Callbacks != nil {
		apiInfo.CallbacksInfo = analyzeType(
			reflect.TypeOf(parser.Callbacks).Elem(),
			reflect.TypeOf(parser.Callbacks),
		)
	}

	// 3. 分析 Entity
	fmt.Println("分析 Entity 类型...")
	entity := &manta.Entity{}
	apiInfo.EntityInfo = analyzeType(
		reflect.TypeOf(entity).Elem(),
		reflect.TypeOf(entity),
	)

	// 4. 分析 GameEvent
	fmt.Println("分析 GameEvent 类型...")
	gameEvent := &manta.GameEvent{}
	apiInfo.GameEventInfo = analyzeType(
		reflect.TypeOf(gameEvent).Elem(),
		reflect.TypeOf(gameEvent),
	)

	// 5. 收集 DOTA 常量
	fmt.Println("收集 DOTA 常量...")
	collectDotaConstants(&apiInfo)

	// 6. 收集实际数据样本
	fmt.Println("收集实际数据样本...")
	collectSampleData(parser, &apiInfo)

	// 7. 保存为 JSON
	outputFile := "manta_api_complete.json"
	jsonData, err := json.MarshalIndent(apiInfo, "", "  ")
	if err != nil {
		log.Fatalf("JSON 编码失败: %v", err)
	}

	err = os.WriteFile(outputFile, jsonData, 0644)
	if err != nil {
		log.Fatalf("写入文件失败: %v", err)
	}

	fmt.Printf("\nAPI 信息已保存到: %s\n", outputFile)

	// 8. 同时生成一个更易读的文本版本
	generateReadableDoc(&apiInfo)

	fmt.Println("\n========================================")
	fmt.Println("导出完成！")
	fmt.Println("- JSON 格式: manta_api_complete.json")
	fmt.Println("- 文档格式: manta_api_doc.txt")
	fmt.Println("========================================")
}

// 分析类型信息
func analyzeType(structType, ptrType reflect.Type) TypeInfo {
	info := TypeInfo{
		Fields:  []FieldInfo{},
		Methods: []MethodInfo{},
	}

	// 分析字段
	if structType.Kind() == reflect.Struct {
		for i := 0; i < structType.NumField(); i++ {
			field := structType.Field(i)
			if field.IsExported() {
				info.Fields = append(info.Fields, FieldInfo{
					Name: field.Name,
					Type: formatType(field.Type),
				})
			}
		}
	}

	// 分析方法
	for i := 0; i < ptrType.NumMethod(); i++ {
		method := ptrType.Method(i)
		methodInfo := MethodInfo{
			Name:       method.Name,
			Parameters: []string{},
			Returns:    []string{},
		}

		funcType := method.Type
		// 参数（跳过 receiver）
		for j := 1; j < funcType.NumIn(); j++ {
			methodInfo.Parameters = append(methodInfo.Parameters, formatType(funcType.In(j)))
		}
		// 返回值
		for j := 0; j < funcType.NumOut(); j++ {
			methodInfo.Returns = append(methodInfo.Returns, formatType(funcType.Out(j)))
		}

		// 构建签名
		params := strings.Join(methodInfo.Parameters, ", ")
		returns := ""
		if len(methodInfo.Returns) > 0 {
			if len(methodInfo.Returns) == 1 {
				returns = " " + methodInfo.Returns[0]
			} else {
				returns = " (" + strings.Join(methodInfo.Returns, ", ") + ")"
			}
		}
		methodInfo.Signature = fmt.Sprintf("%s(%s)%s", method.Name, params, returns)

		info.Methods = append(info.Methods, methodInfo)
	}

	return info
}

// 格式化类型
func formatType(t reflect.Type) string {
	switch t.Kind() {
	case reflect.Ptr:
		return "*" + formatType(t.Elem())
	case reflect.Func:
		return formatFuncType(t)
	case reflect.Interface:
		if t.Name() != "" {
			return t.Name()
		}
		return "interface{}"
	case reflect.Slice:
		return "[]" + formatType(t.Elem())
	case reflect.Map:
		return fmt.Sprintf("map[%s]%s", formatType(t.Key()), formatType(t.Elem()))
	default:
		if t.PkgPath() != "" && t.Name() != "" {
			// 简化包路径
			pkgParts := strings.Split(t.PkgPath(), "/")
			pkgName := pkgParts[len(pkgParts)-1]
			return pkgName + "." + t.Name()
		}
		if t.Name() != "" {
			return t.Name()
		}
		return t.String()
	}
}

// 格式化函数类型
func formatFuncType(t reflect.Type) string {
	params := []string{}
	for i := 0; i < t.NumIn(); i++ {
		params = append(params, formatType(t.In(i)))
	}
	
	returns := []string{}
	for i := 0; i < t.NumOut(); i++ {
		returns = append(returns, formatType(t.Out(i)))
	}
	
	result := "func(" + strings.Join(params, ", ") + ")"
	if len(returns) > 0 {
		if len(returns) == 1 {
			result += " " + returns[0]
		} else {
			result += " (" + strings.Join(returns, ", ") + ")"
		}
	}
	return result
}

// 收集 DOTA 常量
func collectDotaConstants(apiInfo *APIInfo) {
	// 尝试获取一些已知的常量类型
	// 注意：这需要手动添加，因为 Go 的反射不能直接获取包级常量
	
	// COMBATLOG 类型示例
	apiInfo.DotaConstants["DOTA_COMBATLOG_DAMAGE"] = 0
	apiInfo.DotaConstants["DOTA_COMBATLOG_HEAL"] = 1
	apiInfo.DotaConstants["DOTA_COMBATLOG_MODIFIER_ADD"] = 2
	apiInfo.DotaConstants["DOTA_COMBATLOG_MODIFIER_REMOVE"] = 3
	apiInfo.DotaConstants["DOTA_COMBATLOG_DEATH"] = 4
	apiInfo.DotaConstants["DOTA_COMBATLOG_ABILITY"] = 5
	apiInfo.DotaConstants["DOTA_COMBATLOG_ITEM"] = 6
	apiInfo.DotaConstants["DOTA_COMBATLOG_GOLD"] = 11
	apiInfo.DotaConstants["DOTA_COMBATLOG_GAME_STATE"] = 12
	apiInfo.DotaConstants["DOTA_COMBATLOG_XP"] = 13
	apiInfo.DotaConstants["DOTA_COMBATLOG_PURCHASE"] = 14
	apiInfo.DotaConstants["DOTA_COMBATLOG_BUYBACK"] = 15
	
	// 游戏模式
	apiInfo.DotaConstants["DOTA_GAMEMODE_NONE"] = 0
	apiInfo.DotaConstants["DOTA_GAMEMODE_AP"] = 1
	apiInfo.DotaConstants["DOTA_GAMEMODE_CM"] = 2
	apiInfo.DotaConstants["DOTA_GAMEMODE_RD"] = 3
	apiInfo.DotaConstants["DOTA_GAMEMODE_SD"] = 4
	apiInfo.DotaConstants["DOTA_GAMEMODE_AR"] = 5
	apiInfo.DotaConstants["DOTA_GAMEMODE_TURBO"] = 23
	
	// 队伍
	apiInfo.DotaConstants["DOTA_TEAM_NOTEAM"] = 0
	apiInfo.DotaConstants["DOTA_TEAM_SPECTATOR"] = 1
	apiInfo.DotaConstants["DOTA_TEAM_GOODGUYS"] = 2
	apiInfo.DotaConstants["DOTA_TEAM_BADGUYS"] = 3
}

// 收集实际数据样本
func collectSampleData(parser *manta.Parser, apiInfo *APIInfo) {
	entityClasses := make(map[string]bool)
	gameEvents := make(map[string]bool)
	
	// 收集实体类和属性
	parser.Callbacks.OnCSVCMsg_PacketEntities(func(m *dota.CSVCMsg_PacketEntities) error {
		// 只在特定 tick 收集，避免太多数据
		if parser.Tick == 1000 || parser.Tick == 5000 || parser.Tick == 10000 {
			entities := parser.FilterEntity(func(e *manta.Entity) bool {
				return e != nil
			})
			
			for _, entity := range entities {
				className := entity.GetClassName()
				entityClasses[className] = true
				
				// 收集前几个实体的属性作为样本
				if len(apiInfo.SampleData.EntityProperties) < 10 {
					if strings.HasPrefix(className, "CDOTA_Unit_Hero_") ||
					   className == "CDOTA_PlayerResource" ||
					   strings.Contains(className, "GameRules") {
						
						props := []string{}
						entityMap := entity.Map()
						for key := range entityMap {
							props = append(props, key)
						}
						sort.Strings(props)
						
						// 只保存前50个属性
						if len(props) > 50 {
							props = props[:50]
						}
						
						apiInfo.SampleData.EntityProperties[className] = props
					}
				}
			}
		}
		return nil
	})
	
	// 收集游戏事件
	commonEvents := []string{
		"dota_combatlog",
		"entity_killed",
		"entity_hurt",
		"dota_player_kill",
		"dota_chat_event",
		"dota_item_purchased",
		"dota_hero_levelup",
		"dota_player_pick_hero",
		"game_rules_state_change",
		"dota_tower_kill",
		"dota_roshan_kill",
	}
	
	for _, event := range commonEvents {
		parser.OnGameEvent(event, func(m *manta.GameEvent) error {
			gameEvents[event] = true
			return nil
		})
	}
	
	// 解析一部分文件来收集数据
	fmt.Println("正在解析文件以收集样本数据...")
	parser.Start()
	
	// 转换为数组
	for className := range entityClasses {
		apiInfo.SampleData.EntityClasses = append(apiInfo.SampleData.EntityClasses, className)
	}
	sort.Strings(apiInfo.SampleData.EntityClasses)
	
	for event := range gameEvents {
		apiInfo.SampleData.GameEvents = append(apiInfo.SampleData.GameEvents, event)
	}
	sort.Strings(apiInfo.SampleData.GameEvents)
}

// 生成易读的文档
func generateReadableDoc(apiInfo *APIInfo) {
	file, err := os.Create("manta_api_doc.txt")
	if err != nil {
		log.Printf("无法创建文档文件: %v", err)
		return
	}
	defer file.Close()

	fmt.Fprintln(file, "========================================")
	fmt.Fprintln(file, "Manta Parser API 文档")
	fmt.Fprintln(file, "========================================\n")

	// Parser 方法
	fmt.Fprintln(file, "=== Parser 方法 ===")
	for _, method := range apiInfo.ParserInfo.Methods {
		fmt.Fprintf(file, "parser.%s\n", method.Signature)
	}

	// Callbacks 方法
	fmt.Fprintln(file, "\n=== Callbacks 方法 (回调函数) ===")
	for _, method := range apiInfo.CallbacksInfo.Methods {
		if strings.HasPrefix(method.Name, "On") {
			fmt.Fprintf(file, "parser.Callbacks.%s\n", method.Signature)
		}
	}

	// Entity 方法
	fmt.Fprintln(file, "\n=== Entity 方法 ===")
	for _, method := range apiInfo.EntityInfo.Methods {
		fmt.Fprintf(file, "entity.%s\n", method.Signature)
	}

	// GameEvent 方法
	fmt.Fprintln(file, "\n=== GameEvent 方法 ===")
	for _, method := range apiInfo.GameEventInfo.Methods {
		fmt.Fprintf(file, "gameEvent.%s\n", method.Signature)
	}

	// DOTA 常量
	fmt.Fprintln(file, "\n=== DOTA 常量 ===")
	constants := []string{}
	for name := range apiInfo.DotaConstants {
		constants = append(constants, name)
	}
	sort.Strings(constants)
	for _, name := range constants {
		fmt.Fprintf(file, "%s = %d\n", name, apiInfo.DotaConstants[name])
	}

	// 实体类列表
	fmt.Fprintln(file, "\n=== 发现的实体类 ===")
	for _, className := range apiInfo.SampleData.EntityClasses {
		fmt.Fprintln(file, className)
	}

	// 实体属性样本
	fmt.Fprintln(file, "\n=== 实体属性样本 ===")
	for className, props := range apiInfo.SampleData.EntityProperties {
		fmt.Fprintf(file, "\n%s:\n", className)
		for _, prop := range props {
			fmt.Fprintf(file, "  %s\n", prop)
		}
	}

	// 游戏事件
	fmt.Fprintln(file, "\n=== 游戏事件 ===")
	for _, event := range apiInfo.SampleData.GameEvents {
		fmt.Fprintln(file, event)
	}

	fmt.Println("文档已生成: manta_api_doc.txt")
}