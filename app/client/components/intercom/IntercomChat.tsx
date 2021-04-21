import * as React from "react";
import { MessageOutlined } from "@ant-design/icons";
import { useIntercom } from "react-use-intercom";

export const IntercomChat = () => {
  const { showNewMessages } = useIntercom();
  const handleNewMessages = () => showNewMessages();

  return (
    <a onClick={handleNewMessages} target="_blank">
      <MessageOutlined translate={""} /> Contact Support
    </a>
  );
};
