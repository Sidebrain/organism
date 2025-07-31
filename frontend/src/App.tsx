import { HumanArea } from "./components/HumanArea";
import { GenerativeArea } from "./components/GenerativeArea";
import { AppProvider, useAppContext } from "./context/AppContext";
import { useSocket } from "./hooks/useSocket";
import { useEffect, useRef } from "react";

function AppContainer() {
  const { showGenerative, settings } = useAppContext();
  // to trigger the useeffect
  console.log("AppContainer rendered, useSocekt being called next.");
  const { connect, disconnect } = useSocket();
  const hasConnectedRef = useRef(false);

  useEffect(() => {
    if (!hasConnectedRef.current) {
      connect();
      hasConnectedRef.current = true;
    }
    return () => {
      disconnect();
      hasConnectedRef.current = false;
    };
  }, []);

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Mobile View */}
      <div className="md:hidden h-full">
        <div
          className={`h-full transition-transform duration-300 ${
            showGenerative ? "-translate-x-full" : "translate-x-0"
          }`}
        >
          <HumanArea />
        </div>
        <div
          className={`absolute inset-0 transition-transform duration-300 ${
            showGenerative ? "translate-x-0" : "translate-x-full"
          }`}
        >
          <GenerativeArea />
        </div>
      </div>

      {/* Desktop View */}
      <div className="hidden md:flex h-full">
        {settings.generativeOnRight ? (
          <>
            <div className="w-1/2">
              <HumanArea />
            </div>
            <div className="w-1/2">
              <GenerativeArea />
            </div>
          </>
        ) : (
          <>
            <div className="w-1/2">
              <GenerativeArea />
            </div>
            <div className="w-1/2">
              <HumanArea />
            </div>
          </>
        )}
      </div>
    </div>
  );
}

const App = () => {
  return (
    <AppProvider>
      <AppContainer />
    </AppProvider>
  );
};

export default App;
