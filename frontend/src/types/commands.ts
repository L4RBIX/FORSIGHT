/**
 * Frontend -> backend messages, sent over the same WebSocket the backend
 * streams TelemetryFrame on. Only relevant in Live mode — Mock mode drives
 * MockEngine directly and never touches the socket.
 */
export type ForesightCommand = { type: 'scan' } | { type: 'propose_action'; text: string }
