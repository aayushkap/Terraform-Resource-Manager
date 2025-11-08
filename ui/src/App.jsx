import React from "react";
import TabSwitcher from "./components/TabSwitcher";
import InfraView from "./tabs/Infrastructure";
import "./App.css";

export default function App() {
  return (
    <section className="application-container">
      <TabSwitcher />
      <main className="application-section">
        <InfraView />
      </main>
    </section>
  );
}
