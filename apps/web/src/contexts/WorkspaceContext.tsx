"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { listWorkspaces, getWorkspaceId, saveWorkspaceId, getToken } from "@/lib/api";

export interface Workspace {
  id: number;
  name: string;
}

interface WorkspaceContextProps {
  workspaces: Workspace[];
  activeWorkspace: Workspace | null;
  setActiveWorkspace: (workspace: Workspace) => void;
  isLoading: boolean;
  refreshWorkspaces: () => Promise<void>;
}

const WorkspaceContext = createContext<WorkspaceContextProps | undefined>(undefined);

export function WorkspaceProvider({ children }: { children: React.ReactNode }) {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [activeWorkspace, setActiveWorkspaceState] = useState<Workspace | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshWorkspaces = async () => {
    if (!getToken()) {
      setIsLoading(false);
      return;
    }
    try {
      const data = await listWorkspaces();
      setWorkspaces(data);

      const savedId = getWorkspaceId();
      let active = data.find((w: Workspace) => w.id.toString() === savedId);

      if (!active && data.length > 0) {
        active = data[0];
        saveWorkspaceId(active.id.toString());
      }

      setActiveWorkspaceState(active || null);
    } catch (error) {
      console.error("Failed to load workspaces:", error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    refreshWorkspaces();
  }, []);

  const setActiveWorkspace = (workspace: Workspace) => {
    saveWorkspaceId(workspace.id.toString());
    setActiveWorkspaceState(workspace);
    // Reload the page to reset state and fetch new data
    window.location.reload();
  };

  return (
    <WorkspaceContext.Provider
      value={{
        workspaces,
        activeWorkspace,
        setActiveWorkspace,
        isLoading,
        refreshWorkspaces,
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspace() {
  const context = useContext(WorkspaceContext);
  if (context === undefined) {
    throw new Error("useWorkspace must be used within a WorkspaceProvider");
  }
  return context;
}
