import UploadForm from "./components/UploadForm";

function App() {
  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-2xl bg-white rounded-2xl shadow-sm border border-slate-200 p-8">
        
        <header className="mb-8 text-center">
          <h1 className="text-3xl font-semibold tracking-tight">
            ChangeAnyFile<span className="text-blue-600">.ai</span>
          </h1>
          <p className="mt-2 text-sm text-slate-500">
            Convert, compress, and transform files using AI prompts
          </p>
        </header>

        <UploadForm />

      </div>
    </div>
  );
}

export default App;
