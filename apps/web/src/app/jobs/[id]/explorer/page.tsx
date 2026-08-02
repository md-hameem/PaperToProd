"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  ChevronLeft,
  Folder,
  File,
  FileText,
  Terminal,
  BookOpen,
  Info,
  Code2
} from "lucide-react";
import styles from "./explorer.module.css";
import { useWorkspace } from "@/contexts/WorkspaceContext";
import { getArtifactTree, getArtifactFile } from "@/lib/api";

type TreeNode = {
  name: string;
  type: "file" | "directory";
  path?: string;
  children?: TreeNode[];
  has_annotations?: boolean;
};

type Annotation = {
  line: number;
  paper_text: string;
  section: string;
};

export default function RepositoryExplorer() {
  const params = useParams();
  const router = useRouter();
  const { currentWorkspace } = useWorkspace();
  const jobId = params.id as string;

  const [tree, setTree] = useState<TreeNode | null>(null);
  const [activeFile, setActiveFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string>("");
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [activeAnnotationLine, setActiveAnnotationLine] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (currentWorkspace && jobId) {
      loadTree();
    }
  }, [currentWorkspace, jobId]);

  const loadTree = async () => {
    try {
      const data = await getArtifactTree(currentWorkspace!.id.toString(), jobId);
      setTree(data);
      setLoading(false);
    } catch (err) {
      console.error("Failed to load artifact tree", err);
      setLoading(false);
    }
  };

  const handleFileClick = async (path: string) => {
    if (activeFile === path) return;
    setActiveFile(path);
    setActiveAnnotationLine(null);
    setFileContent("Loading...");
    setAnnotations([]);

    try {
      const data = await getArtifactFile(currentWorkspace!.id.toString(), jobId, path);
      setFileContent(data.content);
      setAnnotations(data.annotations || []);
    } catch (err) {
      setFileContent("Failed to load file content.");
    }
  };

  const renderTree = (node: TreeNode, depth: number = 0) => {
    const isFile = node.type === "file";

    return (
      <div key={node.path || node.name}>
        <div
          className={`${styles.treeNode} ${activeFile === node.path ? styles.active : ""}`}
          style={{ paddingLeft: `${depth * 16 + 16}px` }}
          onClick={() => isFile && node.path && handleFileClick(node.path)}
        >
          <span className={styles.treeIcon}>
            {isFile ? <File size={16} /> : <Folder size={16} fill="currentColor" opacity={0.7} />}
          </span>
          <span>{node.name}</span>
          {isFile && node.has_annotations && <div className={styles.annotationDot} />}
        </div>
        {node.children && (
          <div>
            {node.children.map(child => renderTree(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return <div className={styles.layout}>Loading Explorer...</div>;
  }

  // Render code lines with possible annotations
  const codeLines = fileContent.split('\n');

  return (
    <div className={styles.layout}>
      {/* Top Header */}
      <header className={styles.explorerHeader}>
        <div className={styles.headerLeft}>
          <button className={styles.backBtn} onClick={() => router.push(`/jobs/${jobId}`)}>
            <ChevronLeft size={24} />
          </button>
          <div>
            <h1 className={styles.jobTitle}>Repository Explorer</h1>
            <span className={styles.jobBadge}>Job #{jobId}</span>
          </div>
        </div>
      </header>

      {/* Main Workspace */}
      <div className={styles.workspace}>
        {/* Left: File Tree */}
        <div className={styles.sidebar}>
          <div className={styles.sidebarHeader}>Files</div>
          <div className={styles.fileTree}>
            {tree && renderTree(tree)}
          </div>
        </div>

        {/* Center: Editor */}
        <div className={styles.editor}>
          <div className={styles.editorHeader}>
            <Terminal size={16} style={{ marginRight: 8 }} />
            {activeFile || "Select a file"}
          </div>
          <div className={styles.editorContent}>
            <AnimatePresence mode="wait">
              {activeFile ? (
                <motion.pre
                  key={activeFile}
                  className={styles.codeArea}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.15 }}
                >
                  {codeLines.map((line, idx) => {
                    const lineNum = idx + 1;
                    const annotation = annotations.find(a => a.line === lineNum);
                    const isAnnotated = !!annotation;
                    const isActive = activeAnnotationLine === lineNum;

                    return (
                      <div
                        key={idx}
                        className={`${styles.codeLine} ${isAnnotated ? styles.annotatedLine : ""} ${isActive ? styles.activeAnnotation : ""}`}
                        onClick={() => isAnnotated && setActiveAnnotationLine(lineNum)}
                      >
                        <div className={styles.lineNumber}>{lineNum}</div>
                        <div className={styles.lineContent}>{line}</div>
                      </div>
                    );
                  })}
                </motion.pre>
              ) : (
                <div className={styles.emptyPanel} style={{ height: '100%', color: '#484f58' }}>
                  <Code2 size={48} opacity={0.5} />
                  <p>Select a file from the sidebar to view its contents.</p>
                </div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Right: Annotations */}
        <div className={styles.panel}>
          <div className={styles.panelHeader}>
            <BookOpen size={16} />
            Paper Traceability
          </div>
          <div className={styles.panelContent}>
            {!activeFile ? (
              <div className={styles.emptyPanel}>
                <Info size={32} opacity={0.5} />
                <p>Select a file to see links to the original paper.</p>
              </div>
            ) : annotations.length === 0 ? (
              <div className={styles.emptyPanel}>
                <p>No paper traceability annotations for this file.</p>
              </div>
            ) : activeAnnotationLine ? (
              <AnimatePresence mode="wait">
                <motion.div
                  key={activeAnnotationLine}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.2 }}
                >
                  {annotations.filter(a => a.line === activeAnnotationLine).map((a, i) => (
                    <div key={i} className={styles.annotationCard}>
                      <div className={styles.annotationSection}>From Section: {a.section}</div>
                      <blockquote className={styles.annotationText}>"{a.paper_text}"</blockquote>
                    </div>
                  ))}
                </motion.div>
              </AnimatePresence>
            ) : (
              <div className={styles.emptyPanel}>
                <Info size={32} opacity={0.5} />
                <p>Click on highlighted lines in the code to view paper references.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
