import React from "react";
import TabSwitcher from "./components/TabSwitcher";
import InfraView from "./tabs/Infrastructure";
import Observability from "./tabs/Observability";

import "./App.css";
import { useAppSelector } from "@/store/hooks";

export default function App() {
  const tab = useAppSelector((s) => s.tab);

  return (
    <section className="application-container">
      <TabSwitcher />
      <main className="application-section">
        {tab === "infrastructure_management" && <InfraView />}
        {tab === "observability" && <Observability />}
      </main>
    </section>
  );
}
