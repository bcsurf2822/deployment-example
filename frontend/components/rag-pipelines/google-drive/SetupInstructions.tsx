"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";

interface ServiceAccountInfo {
  serviceAccountEmail: string;
  impersonateUser: string | null;
  domainDelegationEnabled: boolean;
  instructions: {
    step1: string;
    step2: string;
    step3: string;
    step4: string;
    step5: string;
    note: string;
  };
  domainDelegationSetup?: {
    warning: string;
    solution: string;
    steps: string[];
  } | null;
  folderId: string;
}

export default function GoogleDriveSetupInstructions() {
  const [serviceInfo, setServiceInfo] = useState<ServiceAccountInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    fetchServiceAccountInfo();
  }, []);

  const fetchServiceAccountInfo = async () => {
    try {
      setIsLoading(true);
      const response = await fetch("/api/google-drive/service-account");
      
      if (!response.ok) {
        throw new Error("Failed to fetch service account information");
      }
      
      const data = await response.json();
      setServiceInfo(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setIsLoading(false);
    }
  };

  const copyEmail = () => {
    if (serviceInfo?.serviceAccountEmail) {
      navigator.clipboard.writeText(serviceInfo.serviceAccountEmail);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const copyFolderId = () => {
    if (serviceInfo?.folderId) {
      navigator.clipboard.writeText(serviceInfo.folderId);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (isLoading) {
    return (
      <div className="p-6 bg-white rounded-lg shadow">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-lg">
        <h3 className="text-red-800 font-semibold mb-2">Error</h3>
        <p className="text-red-600">{error}</p>
      </div>
    );
  }

  if (!serviceInfo) {
    return null;
  }

  return (
    <div className="p-6 bg-blue-50 border border-blue-200 rounded-lg">
      <h3 className="text-lg font-semibold text-blue-900 mb-4">
        Google Drive Setup Instructions
      </h3>
      
      {/* Domain Delegation Status */}
      <div className="mb-6">
        {serviceInfo.domainDelegationEnabled ? (
          <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
            <h4 className="font-semibold text-green-800 mb-2">✅ Domain Delegation Enabled</h4>
            <p className="text-green-700 text-sm mb-2">
              Service account will impersonate: <code className="bg-green-100 px-2 py-1 rounded">{serviceInfo.impersonateUser}</code>
            </p>
            <p className="text-green-600 text-sm">This should resolve service account quota issues.</p>
          </div>
        ) : (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <h4 className="font-semibold text-red-800 mb-2">⚠️ Service Account Quota Issues Detected</h4>
            <p className="text-red-700 text-sm mb-3">
              New Google service accounts have zero storage quota. You'll likely get 403 errors when uploading.
            </p>
            {serviceInfo.domainDelegationSetup && (
              <div>
                <p className="font-medium text-red-800 mb-2">{serviceInfo.domainDelegationSetup.solution}</p>
                <ol className="list-decimal list-inside space-y-1 text-sm text-red-700">
                  {serviceInfo.domainDelegationSetup.steps.map((step, index) => (
                    <li key={index}>{step}</li>
                  ))}
                </ol>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="mb-6">
        <h4 className="font-medium text-blue-800 mb-2">Service Account Email:</h4>
        <div className="flex items-center gap-2">
          <code className="bg-white px-3 py-2 rounded border border-blue-300 text-sm flex-1">
            {serviceInfo.serviceAccountEmail}
          </code>
          <Button
            onClick={copyEmail}
            variant="outline"
            size="sm"
            className="text-blue-600 hover:text-blue-700"
          >
            {copied ? "Copied!" : "Copy"}
          </Button>
        </div>
      </div>

      <div className="mb-6">
        <h4 className="font-medium text-blue-800 mb-2">Current Folder ID:</h4>
        <div className="flex items-center gap-2">
          <code className="bg-white px-3 py-2 rounded border border-blue-300 text-sm flex-1">
            {serviceInfo.folderId}
          </code>
          <Button
            onClick={copyFolderId}
            variant="outline"
            size="sm"
            className="text-blue-600 hover:text-blue-700"
          >
            {copied ? "Copied!" : "Copy"}
          </Button>
        </div>
      </div>

      <div className="space-y-3">
        <h4 className="font-medium text-blue-800">Setup Steps:</h4>
        <ol className="list-decimal list-inside space-y-2 text-blue-700">
          <li>{serviceInfo.instructions.step1}</li>
          <li>{serviceInfo.instructions.step2}</li>
          <li className="font-medium">{serviceInfo.instructions.step3}</li>
          <li>{serviceInfo.instructions.step4}</li>
          <li>{serviceInfo.instructions.step5}</li>
        </ol>
        <div className="mt-4 p-3 bg-blue-100 rounded">
          <p className="text-sm text-blue-800">
            <strong>Note:</strong> {serviceInfo.instructions.note}
          </p>
        </div>
      </div>

      <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded">
        <h4 className="font-medium text-yellow-800 mb-2">Important:</h4>
        <p className="text-sm text-yellow-700">
          If you're still getting quota errors after sharing the folder, make sure:
        </p>
        <ul className="list-disc list-inside mt-2 text-sm text-yellow-700 space-y-1">
          <li>The folder is shared with Editor permissions</li>
          <li>You're using a regular Google Drive folder (not "My Drive" root)</li>
          <li>The folder ID in your environment matches the shared folder</li>
        </ul>
      </div>
    </div>
  );
}