package infrastructure

import (
	"fmt"
	"sync"
	"syscall"
	"time"
	"unsafe"
)

var (
	kernel32                         = syscall.NewLazyDLL("kernel32.dll")
	procCreatePseudoConsole          = kernel32.NewProc("CreatePseudoConsole")
	procClosePseudoConsole           = kernel32.NewProc("ClosePseudoConsole")
	procResizePseudoConsole          = kernel32.NewProc("ResizePseudoConsole")
	procWaitForSingleObject          = kernel32.NewProc("WaitForSingleObject")
	procGetExitCodeProcess           = kernel32.NewProc("GetExitCodeProcess")
	procInitializeProcThreadAttrList = kernel32.NewProc("InitializeProcThreadAttributeList")
	procUpdateProcThreadAttribute    = kernel32.NewProc("UpdateProcThreadAttribute")
	procCreateProcessW               = kernel32.NewProc("CreateProcessW")
	procGetLastError                 = kernel32.NewProc("GetLastError")
)

const (
	INVALID_HANDLE_VALUE              = ^uintptr(0)
	PROC_THREAD_ATTRIBUTE_PSEUDOCONSOLE = 0x00020016
	EXTENDED_STARTUPINFO_PRESENT      = 0x00080000
	STARTF_USESTDHANDLES              = 0x00000100
	BUFFER_SIZE                       = 65536
)

type PTYSession struct {
	id       string
	pid      int
	command  string
	args     []string
	cols     int
	rows     int
	hPC      uintptr
	hPipeIn  uintptr
	hPipeOut uintptr
	pi       processInfo
	closed   bool
	closeMu  sync.RWMutex

	// Output buffer
	outputBuf []byte
	bufMu     sync.Mutex
	readerWg  sync.WaitGroup
}

type processInfo struct {
	hProcess    uintptr
	hThread     uintptr
	dwProcessId uint32
	dwThreadId  uint32
}

type startupInfoEx struct {
	StartupInfo             startupInfo
	ProcThreadAttributeList uintptr
}

type startupInfo struct {
	cb              uint32
	lpReserved      uintptr
	lpDesktop       uintptr
	lpTitle         uintptr
	dwX             uint32
	dwY             uint32
	dwXSize         uint32
	dwYSize         uint32
	dwXCountChars   uint32
	dwYCountChars   uint32
	dwFillAttribute uint32
	dwFlags         uint32
	wShowWindow     uint16
	cbReserved2     uint16
	lpReserved2     uintptr
	hStdInput       uintptr
	hStdOutput      uintptr
	hStdError       uintptr
}

func NewPTYSession(id, command string, args []string, cols, rows int) (*PTYSession, error) {
	var hPipeOutRead, hPipeOutWrite uintptr
	var hPipeInRead, hPipeInWrite uintptr

	sa := &syscall.SecurityAttributes{Length: uint32(unsafe.Sizeof(syscall.SecurityAttributes{})), InheritHandle: 1}

	err := syscall.CreatePipe((*syscall.Handle)(&hPipeOutRead), (*syscall.Handle)(&hPipeOutWrite), sa, 0)
	if err != nil {
		return nil, fmt.Errorf("failed to create output pipe: %w", err)
	}
	err = syscall.CreatePipe((*syscall.Handle)(&hPipeInRead), (*syscall.Handle)(&hPipeInWrite), sa, 0)
	if err != nil {
		syscall.CloseHandle(syscall.Handle(hPipeOutRead))
		syscall.CloseHandle(syscall.Handle(hPipeOutWrite))
		return nil, fmt.Errorf("failed to create input pipe: %w", err)
	}

	var hPC uintptr
	size := uint32(uint16(rows))<<16 | uint32(uint16(cols))
	ret, _, _ := procCreatePseudoConsole.Call(
		uintptr(size), hPipeOutRead, hPipeInWrite, 0,
		uintptr(unsafe.Pointer(&hPC)),
	)
	if ret != 0 || hPC == 0 || hPC == INVALID_HANDLE_VALUE {
		syscall.CloseHandle(syscall.Handle(hPipeOutRead))
		syscall.CloseHandle(syscall.Handle(hPipeOutWrite))
		syscall.CloseHandle(syscall.Handle(hPipeInRead))
		syscall.CloseHandle(syscall.Handle(hPipeInWrite))
		return nil, fmt.Errorf("CreatePseudoConsole failed (ret=%d)", ret)
	}

	cmdLine := command
	for _, a := range args {
		cmdLine += " " + a
	}

	var attrSize uint32
	procInitializeProcThreadAttrList.Call(0, 1, 0, uintptr(unsafe.Pointer(&attrSize)))
	attrList := make([]byte, attrSize)
	procInitializeProcThreadAttrList.Call(
		uintptr(unsafe.Pointer(&attrList[0])), 1, 0,
		uintptr(unsafe.Pointer(&attrSize)),
	)
	procUpdateProcThreadAttribute.Call(
		uintptr(unsafe.Pointer(&attrList[0])), 0,
		PROC_THREAD_ATTRIBUTE_PSEUDOCONSOLE, hPC,
		unsafe.Sizeof(hPC), 0, 0,
	)

	var si startupInfoEx
	si.StartupInfo.cb = uint32(unsafe.Sizeof(si))
	si.StartupInfo.dwFlags = STARTF_USESTDHANDLES
	si.StartupInfo.hStdInput = hPipeInRead
	si.StartupInfo.hStdOutput = hPipeOutWrite
	si.StartupInfo.hStdError = hPipeOutWrite
	si.ProcThreadAttributeList = uintptr(unsafe.Pointer(&attrList[0]))

	cmdLineUTF16, _ := syscall.UTF16PtrFromString(cmdLine)
	var pi processInfo
	ret, _, _ = procCreateProcessW.Call(
		0, uintptr(unsafe.Pointer(cmdLineUTF16)),
		0, 0, 1, EXTENDED_STARTUPINFO_PRESENT,
		0, 0,
		uintptr(unsafe.Pointer(&si)),
		uintptr(unsafe.Pointer(&pi)),
	)
	if ret == 0 {
		procClosePseudoConsole.Call(hPC)
		syscall.CloseHandle(syscall.Handle(hPipeOutRead))
		syscall.CloseHandle(syscall.Handle(hPipeOutWrite))
		syscall.CloseHandle(syscall.Handle(hPipeInRead))
		syscall.CloseHandle(syscall.Handle(hPipeInWrite))
		lastErr, _, _ := procGetLastError.Call()
		return nil, fmt.Errorf("CreateProcessW failed (err=%d)", lastErr)
	}

	syscall.CloseHandle(syscall.Handle(hPipeInRead))
	syscall.CloseHandle(syscall.Handle(hPipeOutWrite))

	session := &PTYSession{
		id:        id,
		pid:       int(pi.dwProcessId),
		command:   command,
		args:      args,
		cols:      cols,
		rows:      rows,
		hPC:       hPC,
		hPipeIn:   hPipeInWrite,
		hPipeOut:  hPipeOutRead,
		pi:        pi,
		outputBuf: make([]byte, 0, BUFFER_SIZE),
	}

	// Start background reader goroutine
	session.readerWg.Add(1)
	go session.readLoop()

	return session, nil
}

func (s *PTYSession) readLoop() {
	defer s.readerWg.Done()
	buf := make([]byte, 4096)
	for {
		s.closeMu.RLock()
		if s.closed || s.hPipeOut == 0 {
			s.closeMu.RUnlock()
			return
		}
		h := s.hPipeOut
		s.closeMu.RUnlock()

		var read uint32
		err := syscall.ReadFile(syscall.Handle(h), buf, &read, nil)
		if err != nil {
			time.Sleep(50 * time.Millisecond)
			continue
		}
		if read > 0 {
			s.bufMu.Lock()
			s.outputBuf = append(s.outputBuf, buf[:read]...)
			if len(s.outputBuf) > BUFFER_SIZE {
				s.outputBuf = s.outputBuf[len(s.outputBuf)-BUFFER_SIZE:]
			}
			s.bufMu.Unlock()
		}
	}
}

func (s *PTYSession) PID() int {
	return s.pid
}

func (s *PTYSession) ReadOutput() ([]byte, error) {
	s.bufMu.Lock()
	defer s.bufMu.Unlock()
	if len(s.outputBuf) == 0 {
		return nil, nil
	}
	data := make([]byte, len(s.outputBuf))
	copy(data, s.outputBuf)
	s.outputBuf = s.outputBuf[:0]
	return data, nil
}

func (s *PTYSession) WriteInput(data []byte) error {
	s.closeMu.RLock()
	defer s.closeMu.RUnlock()
	if s.closed || s.hPipeIn == 0 {
		return fmt.Errorf("session closed")
	}
	var written uint32
	return syscall.WriteFile(syscall.Handle(s.hPipeIn), data, &written, nil)
}

func (s *PTYSession) Resize(cols, rows int) error {
	s.closeMu.RLock()
	defer s.closeMu.RUnlock()
	if s.closed {
		return fmt.Errorf("session closed")
	}
	s.cols = cols
	s.rows = rows
	size := uint32(uint16(rows))<<16 | uint32(uint16(cols))
	procResizePseudoConsole.Call(s.hPC, uintptr(size))
	return nil
}

func (s *PTYSession) Close() error {
	s.closeMu.Lock()
	s.closed = true
	s.closeMu.Unlock()

	if s.hPC != 0 {
		procClosePseudoConsole.Call(s.hPC)
		s.hPC = 0
	}
	if s.hPipeOut != 0 {
		syscall.CloseHandle(syscall.Handle(s.hPipeOut))
		s.hPipeOut = 0
	}
	if s.hPipeIn != 0 {
		syscall.CloseHandle(syscall.Handle(s.hPipeIn))
		s.hPipeIn = 0
	}
	s.readerWg.Wait()

	if s.pi.hProcess != 0 {
		procWaitForSingleObject.Call(s.pi.hProcess, 5000)
		syscall.CloseHandle(syscall.Handle(s.pi.hProcess))
		syscall.CloseHandle(syscall.Handle(s.pi.hThread))
	}
	return nil
}

type PTYManager struct {
	sessions map[string]*PTYSession
	mu       sync.RWMutex
}

func NewPTYManager() *PTYManager {
	return &PTYManager{
		sessions: make(map[string]*PTYSession),
	}
}

func (m *PTYManager) Spawn(id, command string, args []string, cols, rows int) (*PTYSession, error) {
	session, err := NewPTYSession(id, command, args, cols, rows)
	if err != nil {
		return nil, err
	}
	m.mu.Lock()
	m.sessions[id] = session
	m.mu.Unlock()
	return session, nil
}

func (m *PTYManager) Get(id string) (*PTYSession, bool) {
	m.mu.RLock()
	defer m.mu.RUnlock()
	s, ok := m.sessions[id]
	return s, ok
}

func (m *PTYManager) Remove(id string) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	if s, ok := m.sessions[id]; ok {
		s.Close()
		delete(m.sessions, id)
	}
	return nil
}

func (m *PTYManager) IsRunning(id string) bool {
	m.mu.RLock()
	s, ok := m.sessions[id]
	m.mu.RUnlock()
	if !ok {
		return false
	}
	if s.pi.hProcess == 0 {
		return false
	}
	var exitCode uint32
	ret, _, _ := procGetExitCodeProcess.Call(s.pi.hProcess, uintptr(unsafe.Pointer(&exitCode)))
	if ret == 0 {
		return false
	}
	return exitCode == 259
}
