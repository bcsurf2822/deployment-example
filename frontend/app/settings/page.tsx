"use client";

import { useState } from "react";
import SettingsContainer from "@/components/settings/SettingsContainer";
import SettingsMenu from "@/components/settings/SettingsMenu";
import { TestSocketSettings } from "@/components/settings/SettingsItems";

export default function SettingsPage() {
  const [activeSection, setActiveSection] = useState("general");

  const sections = [
    {
      id: "general",
      label: "General",
      component: <TestSocketSettings />
    }
  ];

  return (
    <SettingsContainer>
      <SettingsMenu 
        sections={sections}
        activeSection={activeSection}
        onSectionChange={setActiveSection}
      />
    </SettingsContainer>
  );
}