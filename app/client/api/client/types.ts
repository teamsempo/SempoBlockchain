export type Method =
  | "put"
  | "PUT"
  | "post"
  | "POST"
  | "get"
  | "GET"
  | "delete"
  | "DELETE";

interface Body {
  [key: string]: string;
}

export interface ApiClientType {
  url: string;
  method: Method;
  isAuthed?: boolean;
  isTFA?: boolean;
  isForm?: boolean;
  query?: null | object;
  body?: null | Body;
  path?: null | number;
  errorHandling?: boolean;
}

export interface API {
  query?: null | object;
  path?: null | number;
  body?: null | Body;
}
