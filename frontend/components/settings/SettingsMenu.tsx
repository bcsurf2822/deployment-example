"use client";

import { ReactNode } from "react";

interface SettingsSection {
  id: string;
  label: string;
  component: ReactNode;
}

interface SettingsMenuProps {
  sections: SettingsSection[];
  activeSection: string;
  onSectionChange: (sectionId: string) => void;
}

export default function SettingsMenu({ 
  sections, 
  activeSection, 
  onSectionChange 
}: SettingsMenuProps) {
  return (
    <div className="flex h-full">
      <div className="w-64 border-r border-gray-200 bg-gray-50">
        <nav className="p-4 space-y-1">
          {sections.map((section) => (
            <button
              key={section.id}
              onClick={() => onSectionChange(section.id)}
              className={`w-full text-left px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                activeSection === section.id
                  ? "bg-white text-gray-900 shadow-sm"
                  : "text-gray-600 hover:text-gray-900 hover:bg-white/50"
              }`}
            >
              {section.label}
            </button>
          ))}
        </nav>
      </div>
      <div className="flex-1 p-6">
        {sections.find(s => s.id === activeSection)?.component}
      </div>
    </div>
  );
}