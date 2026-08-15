import { DatasetManager } from "../components/DatasetManager";
import { DocumentManager } from "../components/DocumentManager";

export function DataSourcesPage() {
  return (
    <div className="flex-1 space-y-4 overflow-y-auto p-6">
      <DocumentManager />
      <DatasetManager />
    </div>
  );
}
