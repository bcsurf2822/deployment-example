interface ServerToClientEvents {
  message: (data: unknown) => void;
}

interface ClientToServerEvents {
  message: (data: unknown) => void;
}

export type {
  ServerToClientEvents,
  ClientToServerEvents
};