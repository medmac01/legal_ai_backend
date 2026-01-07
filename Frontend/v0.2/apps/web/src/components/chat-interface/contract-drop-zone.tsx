import { FileUp } from "lucide-react";
import { Button } from "../ui/button";
import React, { DragEvent, useState } from "react";
import { useToast } from "@/hooks/use-toast";

interface ContractDropZoneProps {
  onUpload: (files: FileList, file: File) => void;
  isDocumentUploaded?: boolean;
}

export function ContractDropZone({ onUpload, isDocumentUploaded }: ContractDropZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const { toast } = useToast();

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isDocumentUploaded) {
      setIsDragging(true);
    }
  };

  const handleDragEnter = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isDocumentUploaded) {
      setIsDragging(true);
    }
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    
    if (isDocumentUploaded) {
      toast({
        title: "Document already uploaded",
        description: "Please remove the current document before uploading a new one.",
        duration: 3000,
      });
      return;
    }

    const files = e.dataTransfer.files;
    
    if (files.length === 0) {
      return;
    }

    // Check if files are of acceptable types
    const acceptableTypes = ['.pdf', '.docx', '.txt'];
    const file = files[0];
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
    
    if (!acceptableTypes.includes(fileExtension)) {
      toast({
        title: "Unsupported file type",
        description: `Please upload a PDF, DOCX, or TXT file. Received ${fileExtension} file.`,
        variant: "destructive",
        duration: 5000,
      });
      return;
    }

    onUpload(files, file);
  };

  const handleButtonClick = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.pdf,.docx,.txt';
    input.onchange = (e: any) => {
      const files = e.target.files;
      if (files && files.length > 0) {
        onUpload(files, files[0]);
      }
    };
    input.click();
  };

  return (
    <div
      onDragOver={handleDragOver}
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={`flex flex-col gap-4 items-center transition-all duration-200 ${
        isDragging ? "bg-blue-50 p-8 rounded-xl border-2 border-dashed border-blue-300" : ""
      }`}
    >
      <p className="text-gray-600 text-sm">
        {isDragging ? "Drop your contract document here" : "Start by uploading a contract document"}
      </p>
      <Button
        variant="outline"
        className="text-blue-600 hover:text-blue-700 transition-colors ease-in rounded-2xl flex items-center justify-center gap-2 w-[250px] h-[64px] mx-auto border-blue-200 hover:border-blue-300 hover:bg-blue-50"
        onClick={handleButtonClick}
      >
        Upload Contract
        <FileUp className="h-5 w-5" />
      </Button>
      {isDragging && (
        <p className="text-blue-600 text-xs">Release to upload</p>
      )}
    </div>
  );
}