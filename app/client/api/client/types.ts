export type Method =
  | "put"
  | "PUT"
  | "post"
  | "POST"
  | "get"
  | "GET"
  | "delete"
  | "DELETE";

export interface Body {
  [key: string]: any;
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
