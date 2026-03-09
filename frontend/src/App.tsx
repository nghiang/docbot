import { useCallback, useEffect, useState } from "react";
import type { UploadedFile } from "./types";
import { AuthProvider, useAuth } from "./AuthContext";
import { getDocuments } from "./api";
import UploadPanel from "./components/UploadPanel";
import ProcessingStatus from "./components/ProcessingStatus";
import ChatWindow from "./components/ChatWindow";
import AuthModal from "./components/AuthModal";
import UserMenu from "./components/UserMenu";
import ConversationList from "./components/ConversationList";
import Homepage from "./components/Homepage";

function AppContent() {
  const { isAuthenticated, isLoading } = useAuth();
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authModalMode, setAuthModalMode] = useState<"login" | "register">("login");
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);

  // Load persisted documents on login
  useEffect(() => {
    if (!isAuthenticated) return;
    getDocuments()
      .then((docs) => {
        setFiles(
          docs.map((d) => ({
            id: d.id,
            fileName: d.file_name,
            taskId: d.task_id ?? "",
            status: d.status as UploadedFile["status"],
          }))
        );
      })
      .catch(() => { });
  }, [isAuthenticated]);

  const handleFileUploaded = useCallback((file: UploadedFile) => {
    setFiles((prev) => [file, ...prev]);
  }, []);

  const handleFileUpdate = useCallback((index: number, updated: UploadedFile) => {
    setFiles((prev) => {
      const copy = [...prev];
      copy[index] = updated;
      return copy;
    });
  }, []);

  const openLoginModal = useCallback(() => {
    setAuthModalMode("login");
    setShowAuthModal(true);
  }, []);

  const openRegisterModal = useCallback(() => {
    setAuthModalMode("register");
    setShowAuthModal(true);
  }, []);

  // Show loading state
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-600 border-t-transparent"></div>
      </div>
    );
  }

  // Show homepage for unauthenticated users
  if (!isAuthenticated) {
    return (
      <>
        <Homepage onLoginClick={openLoginModal} onRegisterClick={openRegisterModal} />
        <AuthModal
          isOpen={showAuthModal}
          onClose={() => setShowAuthModal(false)}
          initialMode={authModalMode}
        />
      </>
    );
  }

  // Show main app for authenticated users
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4 shadow-sm">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-bold text-gray-900">
            DocBot
            <span className="ml-2 text-sm font-normal text-gray-500">
              Document QA Chatbot
            </span>
          </h1>
          <UserMenu onLoginClick={openLoginModal} />
        </div>
      </header>

      {/* Main layout */}
      <main className="flex flex-col lg:flex-row h-[calc(100vh-65px)]">
        {/* Left panel */}
        <aside className="w-full lg:w-[380px] border-b lg:border-b-0 lg:border-r border-gray-200 bg-white p-5 overflow-y-auto">
          <UploadPanel onFileUploaded={handleFileUploaded} />
          <ProcessingStatus files={files} onUpdate={handleFileUpdate} />

          <div className="mt-6 pt-6 border-t border-gray-200">
            <ConversationList
              currentConversationId={currentConversationId}
              onSelectConversation={setCurrentConversationId}
            />
          </div>
        </aside>

        {/* Right panel — Chat */}
        <section className="flex-1 p-5 flex flex-col min-h-0">
          <ChatWindow
            conversationId={currentConversationId}
            onConversationChange={setCurrentConversationId}
          />
        </section>
      </main>

      {/* Auth Modal */}
      <AuthModal isOpen={showAuthModal} onClose={() => setShowAuthModal(false)} />
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
