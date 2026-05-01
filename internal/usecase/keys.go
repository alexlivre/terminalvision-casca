package usecase

import (
	"encoding/json"
	"fmt"
	"strings"
)

// KeyMap maps key names to bytes
var KeyMap = map[string][]byte{
	"ctrl+c":      {0x03},           // ETX
	"ctrl+d":      {0x04},           // EOT
	"ctrl+z":      {0x1A},           // SUB
	"ctrl+[":      {0x1B},           // ESC
	"enter":       {'\r', '\n'},     // CRLF
	"escape":      {0x1B},           // ESC
	"tab":         {'\t'},           // TAB
	"backspace":   {0x7F},           // DEL
	"arrow_up":    {0x1B, '[', 'A'}, // VT100
	"arrow_down":  {0x1B, '[', 'B'},
	"arrow_right": {0x1B, '[', 'C'},
	"arrow_left":  {0x1B, '[', 'D'},
	"home":        {0x1B, '[', 'H'},
	"end":         {0x1B, '[', 'F'},
	"page_up":     {0x1B, '[', '5', '~'},
	"page_down":   {0x1B, '[', '6', '~'},
	"delete":      {0x1B, '[', '3', '~'},
	"f1":          {0x1B, '[', 'P'},
	"f2":          {0x1B, '[', 'Q'},
	"f3":          {0x1B, '[', 'R'},
	"f4":          {0x1B, '[', 'S'},
	"f5":          {0x1B, 'O', 'P'},
	"f6":          {0x1B, 'O', 'Q'},
	"f7":          {0x1B, 'O', 'R'},
	"f8":          {0x1B, 'O', 'S'},
	"f9":          {0x1B, '[', '1', '5', '~'},
	"f10":         {0x1B, '[', '1', '7', '~'},
	"f11":         {0x1B, '[', '1', '8', '~'},
	"f12":         {0x1B, '[', '1', '9', '~'},
}

// ParseKeys converts keys interface to bytes
func ParseKeys(keys interface{}) ([]byte, error) {
	switch v := keys.(type) {
	case string:
		return parseStringKeys(v), nil
	case []interface{}:
		var result []byte
		for _, item := range v {
			keyBytes, err := parseKeyEvent(item)
			if err != nil {
				return nil, err
			}
			result = append(result, keyBytes...)
		}
		return result, nil
	default:
		return nil, fmt.Errorf("unsupported keys type: %T", keys)
	}
}

func parseStringKeys(s string) []byte {
	// Check if entire string is a special key
	if bytes, ok := KeyMap[s]; ok {
		return bytes
	}

	// Check for prefix patterns
	lower := toLower(s)
	if bytes, ok := KeyMap[lower]; ok {
		return bytes
	}

	// Handle escape sequences
	result := make([]byte, 0, len(s))
	for i := 0; i < len(s); i++ {
		if s[i] == '\\' && i+1 < len(s) {
			switch s[i+1] {
			case 'r':
				result = append(result, '\r')
				i++
			case 'n':
				result = append(result, '\n')
				i++
			case 't':
				result = append(result, '\t')
				i++
			case '\\':
				result = append(result, '\\')
				i++
			default:
				result = append(result, s[i])
			}
		} else {
			result = append(result, s[i])
		}
	}

	return result
}

func parseKeyEvent(item interface{}) ([]byte, error) {
	switch v := item.(type) {
	case string:
		return parseStringKeys(v), nil
	case map[string]interface{}:
		keyType, _ := v["type"].(string)
		key, _ := v["key"].(string)

		switch keyType {
		case "ctrl":
			// Ctrl+key -> convert to control character
			if len(key) == 1 {
				return []byte{byte(key[0] - 'a' + 1)}, nil
			}
			// Special ctrl combinations
			switch toLower(key) {
			case "c":
				return KeyMap["ctrl+c"], nil
			case "d":
				return KeyMap["ctrl+d"], nil
			case "z":
				return KeyMap["ctrl+z"], nil
			}
			return parseStringKeys(strings.ToLower(key)), nil
		case "alt":
			// Alt is ESC prefix + key
			return append([]byte{0x1B}, []byte(key)...), nil
		case "shift":
			return []byte(key), nil
		default:
			return parseStringKeys(key), nil
		}
	default:
		data, _ := json.Marshal(item)
		return nil, fmt.Errorf("invalid key event: %s", string(data))
	}
}

func toLower(s string) string {
	result := make([]byte, len(s))
	for i := 0; i < len(s); i++ {
		c := s[i]
		if c >= 'A' && c <= 'Z' {
			c += 'a' - 'A'
		}
		result[i] = c
	}
	return string(result)
}