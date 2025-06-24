import React from 'react';
import { cn } from '@/lib/utils';

interface SkeletonProps {
  className?: string;
  children?: React.ReactNode;
}

export function Skeleton({ className, children, ...props }: SkeletonProps & React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("animate-pulse rounded-md bg-muted", className)}
      {...props}
    >
      {children}
    </div>
  );
}

// Skeleton específicos para diferentes componentes
export function DocumentSkeleton() {
  return (
    <div className="bg-card border border-border rounded-lg p-4">
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 mb-2">
            <Skeleton className="w-5 h-5" />
            <Skeleton className="h-4 w-48" />
            <Skeleton className="h-6 w-20 rounded-md" />
          </div>
          
          <div className="flex items-center gap-4 text-sm mb-2">
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-4 w-28" />
          </div>
          
          <Skeleton className="h-3 w-40" />
        </div>
        
        <div className="flex items-center gap-2 ml-4">
          <Skeleton className="w-8 h-8 rounded-lg" />
          <Skeleton className="w-8 h-8 rounded-lg" />
        </div>
      </div>
    </div>
  );
}

export function TemplateSkeleton() {
  return (
    <div className="bg-card border border-border rounded-lg p-4">
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-2">
            <Skeleton className="w-4 h-4" />
            <Skeleton className="h-5 w-32" />
            <Skeleton className="h-5 w-16 rounded-full" />
          </div>
          <Skeleton className="h-3 w-full mb-2" />
          <Skeleton className="h-3 w-3/4" />
        </div>
        <div className="flex gap-1 ml-4">
          <Skeleton className="w-8 h-8 rounded" />
          <Skeleton className="w-8 h-8 rounded" />
          <Skeleton className="w-8 h-8 rounded" />
        </div>
      </div>
      
      <div className="flex items-center gap-2">
        <Skeleton className="h-4 w-12" />
        <Skeleton className="h-5 w-16 rounded-full" />
        <Skeleton className="h-5 w-20 rounded-full" />
      </div>
    </div>
  );
}

export function AnnotationSkeleton() {
  return (
    <div className="border border-border rounded-lg p-3 mb-2">
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <Skeleton className="w-4 h-4" />
          <Skeleton className="h-4 w-24" />
        </div>
        <Skeleton className="w-3 h-3 rounded-full" />
      </div>
      
      <Skeleton className="h-3 w-full mb-1" />
      <Skeleton className="h-3 w-4/5 mb-2" />
      
      <div className="flex items-center justify-between">
        <div className="flex gap-1">
          <Skeleton className="h-4 w-12 rounded-full" />
          <Skeleton className="h-4 w-16 rounded-full" />
        </div>
        <div className="flex gap-1">
          <Skeleton className="w-6 h-6 rounded" />
          <Skeleton className="w-6 h-6 rounded" />
        </div>
      </div>
    </div>
  );
}

export function CategorySkeleton() {
  return (
    <div className="bg-card border border-border rounded-lg p-4">
      <div className="flex items-center gap-3 mb-3">
        <Skeleton className="w-12 h-12 rounded-lg" />
        <div className="flex-1">
          <Skeleton className="h-5 w-32 mb-1" />
          <Skeleton className="h-3 w-48" />
        </div>
        <div className="flex gap-2">
          <Skeleton className="w-8 h-8 rounded" />
          <Skeleton className="w-8 h-8 rounded" />
        </div>
      </div>
      
      <div className="grid grid-cols-3 gap-4 text-center">
        <div>
          <Skeleton className="h-6 w-8 mx-auto mb-1" />
          <Skeleton className="h-3 w-16 mx-auto" />
        </div>
        <div>
          <Skeleton className="h-6 w-8 mx-auto mb-1" />
          <Skeleton className="h-3 w-20 mx-auto" />
        </div>
        <div>
          <Skeleton className="h-6 w-8 mx-auto mb-1" />
          <Skeleton className="h-3 w-16 mx-auto" />
        </div>
      </div>
    </div>
  );
}

// Skeletons para chat y conversaciones
export function ChatMessageSkeleton({ isUser = false }: { isUser?: boolean }) {
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`max-w-[80%] ${isUser ? 'order-1' : 'order-2'}`}>
        <div className={`rounded-lg p-3 ${isUser ? 'bg-purple-600' : 'bg-gray-700'}`}>
          <Skeleton className={`h-4 w-48 mb-2 ${isUser ? 'bg-purple-700' : 'bg-gray-600'}`} />
          <Skeleton className={`h-4 w-32 mb-2 ${isUser ? 'bg-purple-700' : 'bg-gray-600'}`} />
          <Skeleton className={`h-4 w-40 ${isUser ? 'bg-purple-700' : 'bg-gray-600'}`} />
        </div>
        <div className="flex items-center gap-2 mt-1 text-xs text-gray-500">
          <Skeleton className="h-3 w-12 bg-gray-600" />
        </div>
      </div>
    </div>
  );
}

export function ConversationSkeleton() {
  return (
    <div className="group relative">
      <div className="flex items-center gap-2">
        <div className="flex items-start gap-2 flex-1 px-2 py-2 rounded-md">
          <Skeleton className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 bg-gray-600" />
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <Skeleton className="h-4 w-32 bg-gray-600" />
              <Skeleton className="h-3 w-8 bg-gray-600" />
            </div>
            <Skeleton className="h-3 w-24 mt-1 bg-gray-600" />
          </div>
        </div>
      </div>
    </div>
  );
}

export function SidebarSkeleton() {
  return (
    <div className="px-3 pb-3">
      <div className="space-y-1">
        {/* Carpeta skeleton */}
        <div className="mb-2">
          <div className="flex items-center gap-2 px-2 py-2">
            <Skeleton className="w-4 h-4 bg-gray-600" />
            <Skeleton className="w-4 h-4 bg-gray-600" />
            <Skeleton className="h-4 w-20 bg-gray-600" />
            <Skeleton className="h-3 w-4 ml-auto bg-gray-600" />
          </div>
          
          {/* Conversaciones skeleton */}
          <div className="ml-6 mt-1 space-y-1">
            {Array.from({ length: 3 }).map((_, i) => (
              <ConversationSkeleton key={i} />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export function ChatLoadingSkeleton() {
  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      <ChatMessageSkeleton isUser={false} />
      <ChatMessageSkeleton isUser={true} />
      <ChatMessageSkeleton isUser={false} />
      <ChatMessageSkeleton isUser={true} />
      <ChatMessageSkeleton isUser={false} />
    </div>
  );
} 