// filepath: /Users/petrosrapto/Desktop/testing/Langchain/open-canvas/apps/web/src/components/auth/ReadOnlyComposer.tsx
"use client";

import { useState, useEffect, useRef } from "react";
import { SendHorizontalIcon } from "lucide-react";

const PAKTON_PLACEHOLDERS = [
  "What terms are covered in this contract?",
  "Explain the liability clauses in this document",
  "What are my obligations under this agreement?",
  "Summarize the key points of this contract",
  "What are the termination conditions?",
  "Explain the intellectual property rights in this document",
  "What penalties are specified for breach of contract?",
  "What are the payment terms and conditions?",
  "Are there any restrictive covenants in this agreement?",
  "What's the duration of this contract?",
];

// Function to get a random placeholder that's different from the current one
const getRandomPaktonPlaceholder = (currentPlaceholder: string) => {
  let newPlaceholders = PAKTON_PLACEHOLDERS.filter(p => p !== currentPlaceholder);
  return newPlaceholders[Math.floor(Math.random() * newPlaceholders.length)];
};

export const ReadOnlyComposer = () => {
  const [placeholder, setPlaceholder] = useState("");
  const [displayedPlaceholder, setDisplayedPlaceholder] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const placeholderTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const streamingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Initialize with a random placeholder
  useEffect(() => {
    const initialPlaceholder = PAKTON_PLACEHOLDERS[Math.floor(Math.random() * PAKTON_PLACEHOLDERS.length)];
    setPlaceholder(initialPlaceholder);
    setDisplayedPlaceholder("");
    setIsStreaming(true);
    
    return () => {
      if (placeholderTimeoutRef.current) clearTimeout(placeholderTimeoutRef.current);
      if (streamingIntervalRef.current) clearInterval(streamingIntervalRef.current);
    };
  }, []);

  // Handle the streaming effect for placeholders
  useEffect(() => {
    if (isStreaming) {
      let index = 0;
      
      // Clear any existing intervals
      if (streamingIntervalRef.current) {
        clearInterval(streamingIntervalRef.current);
      }
      
      // Set up new streaming interval
      streamingIntervalRef.current = setInterval(() => {
        if (index <= placeholder.length) {
          setDisplayedPlaceholder(placeholder.substring(0, index));
          index++;
        } else {
          setIsStreaming(false);
          if (streamingIntervalRef.current) {
            clearInterval(streamingIntervalRef.current);
          }
          
          // Schedule next placeholder change
          placeholderTimeoutRef.current = setTimeout(() => {
            const nextPlaceholder = getRandomPaktonPlaceholder(placeholder);
            setPlaceholder(nextPlaceholder);
            setDisplayedPlaceholder("");
            setIsStreaming(true);
          }, 5000); // Wait 5 seconds before changing to a new placeholder
        }
      }, 50); // Stream each character at 50ms intervals
    }
    
    return () => {
      if (streamingIntervalRef.current) clearInterval(streamingIntervalRef.current);
    };
  }, [isStreaming, placeholder]);

  return (
    <div className="flex flex-col w-full max-w-2xl mx-auto mt-8 mb-8">
      <div className="focus-within:border-aui-ring/20 flex flex-col w-full min-h-[64px] flex-wrap items-center justify-center border px-2.5 shadow-sm transition-colors ease-in bg-white rounded-2xl">
        <div className="flex flex-row w-full items-center justify-start my-auto">
          <div className="placeholder:text-muted-foreground max-h-40 flex-grow resize-none border-none bg-transparent px-2 py-4 text-sm outline-none focus:ring-0 disabled:cursor-not-allowed text-center placeholder:text-center">
            <span className="text-gray-500">{displayedPlaceholder}{isStreaming && <span className="animate-pulse">|</span>}</span>
          </div>
          <div className="relative group">
            <button 
              className="my-2.5 size-8 p-2 transition-opacity ease-in bg-black text-white rounded-md flex items-center justify-center opacity-80" 
              disabled={true}
            >
              <SendHorizontalIcon size={16} />
            </button>
            <div className="absolute bottom-full mb-2 right-0 w-48 p-2 bg-gray-800 text-white text-xs rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
              Sign in to start a conversation
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};