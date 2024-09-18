DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS setting;
DROP TABLE IF EXISTS session;
DROP TABLE IF EXISTS chats;

CREATE TABLE user (
    id TEXT PRIMARY KEY DEFAULT( uuid() ),
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

CREATE TABLE setting (
    user_id TEXT PRIMARY KEY,
    setting JSON NOT NULL,
    FOREIGN KEY(user_id) REFERENCES user(id)
);

CREATE TABLE session (
    user_id INTEGER NOT NULL,
    token TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES user(id)
);

CREATE TABLE chats (
    id TEXT PRIMARY KEY DEFAULT( uuid() ),
    user_id TEXT NOT NULL,
    message JSON NOT NULL,
    FOREIGN KEY(user_id) REFERENCES user(id)
);
