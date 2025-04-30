// frontend/src/components/Chat/MessageList.js
import React, { useEffect, useRef, memo } from 'react';
import { FixedSizeList as List } from 'react-window';
import AutoSizer from 'react-virtualized-auto-sizer';
import MessageBubble from './MessageBubble';

// Memoize MessageBubble rendering
const MemoizedMessageBubble = memo(MessageBubble);

const MessageList = ({ messages }) => {
  const listRef = useRef(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    if (listRef.current) {
      listRef.current.scrollToItem(messages.length - 1);
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages.length]);

  const Row = ({ index, style }) => (
    <div style={style}>
      <MemoizedMessageBubble message={messages[index]} />
    </div>
  );

  return (
    <div className="flex-grow overflow-hidden bg-gray-100 dark:bg-gray-800">
      <AutoSizer>
        {({ height, width }) => (
          <List
            ref={listRef}
            height={height}
            itemCount={messages.length}
            itemSize={100} // Adjust based on average message height
            width={width}
            className="p-4 scrollbar-thin scrollbar-thumb-gray-400 scrollbar-track-transparent"
          >
            {Row}
          </List>
        )}
      </AutoSizer>
      <div ref={messagesEndRef} />
    </div>
  );
};

export default memo(MessageList);
