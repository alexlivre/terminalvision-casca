package domain

// SpawnRequest represents a spawn request
type SpawnRequest struct {
	Command string   `json:"command"`
	Args    []string `json:"args"`
	Mode    string   `json:"mode"` // "auto", "conpty", "visible"
	Cols    int      `json:"cols"`
	Rows    int      `json:"rows"`
	CWD     string   `json:"cwd"`
}

// SpawnResponse represents a spawn response
type SpawnResponse struct {
	Success    bool   `json:"success"`
	SessionID  string `json:"session_id,omitempty"`
	ModeUsed   string `json:"mode_used,omitempty"`
	PID        int    `json:"pid,omitempty"`
	Command    string `json:"command,omitempty"`
	Error      string `json:"error,omitempty"`
}

// ScreenRequest represents a screen capture request
type ScreenRequest struct {
	Format string `json:"format"` // "text" or "image"
}

// ScreenResponse represents a screen capture response
type ScreenResponse struct {
	Type    string `json:"type"`
	Content string `json:"content,omitempty"`
	Path    string `json:"path,omitempty"`
	Hash    string `json:"hash,omitempty"`
	Width   int    `json:"width,omitempty"`
	Height  int    `json:"height,omitempty"`
}

// KeysRequest represents a keys sending request
type KeysRequest struct {
	Keys interface{} `json:"keys"` // string or []KeyEvent
}

// KeyEvent represents a single key event
type KeyEvent struct {
	Type string `json:"type"` // "key", "ctrl", "alt"
	Key  string `json:"key"`
}

// KeysResponse represents a keys response
type KeysResponse struct {
	Success bool   `json:"success"`
	Error   string `json:"error,omitempty"`
}

// ResizeRequest represents a resize request
type ResizeRequest struct {
	Cols int `json:"cols"`
	Rows int `json:"rows"`
}

// ResizeResponse represents a resize response
type ResizeResponse struct {
	Success bool   `json:"success"`
	Error   string `json:"error,omitempty"`
}

// WaitRequest represents a wait request
type WaitRequest struct {
	Condition string `json:"condition"` // "text:foo" or "stable:3s"
	TimeoutMs int    `json:"timeout_ms"`
}

// WaitResponse represents a wait response
type WaitResponse struct {
	Met      bool `json:"met"`
	WaitedMs int  `json:"waited_ms"`
}

// ListResponse represents a list sessions response
type ListResponse struct {
	Sessions []map[string]interface{} `json:"sessions"`
}

// KillResponse represents a kill response
type KillResponse struct {
	Success bool   `json:"success"`
	Error   string `json:"error,omitempty"`
}

// ErrorResponse represents an error response
type ErrorResponse struct {
	Error string `json:"error"`
}
