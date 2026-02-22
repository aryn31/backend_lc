import { useState, useEffect } from "react";
import axios from "axios";
import Editor from "@monaco-editor/react";

function App() {
  const [code, setCode] = useState("# Write your Python/C++ code here\n");
  const [output, setOutput] = useState(null);
  const [loading, setLoading] = useState(false);
  const [problem, setProblem] = useState(null);
  const [language, setLanguage] = useState("python");

  // Fetch the problem details when the page loads
  useEffect(() => {
    async function fetchProblem() {
      try {
        const res = await axios.get("http://127.0.0.1:8000/problems");
        // For this demo, we just grab the first problem (ID: 1)
        if (res.data.length > 0) {
          setProblem(res.data[0]); 
        }
      } catch (err) {
        console.error("Backend not running?", err);
      }
    }
    fetchProblem();
  }, []);

  const handleSubmit = async () => {
    setLoading(true);
    setOutput(null);
    try {
      const payload = {
        problem_id: 1, // Hardcoded for MVP
        language: language,
        code: code,
      };
      
      const res = await axios.post("http://127.0.0.1:8000/submit", payload);
      setOutput(res.data);
    } catch (err) {
      setOutput({ status: "Error", details: "Could not connect to server." });
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white flex flex-col font-sans">
      
      {/* Navbar */}
      <header className="bg-gray-800 p-4 border-b border-gray-700 flex justify-between items-center">
        <h1 className="text-xl font-bold text-yellow-500">LeetClone 🚀</h1>
        <select 
          className="bg-gray-700 text-white px-3 py-1 rounded border border-gray-600"
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
        >
          <option value="python">Python</option>
          <option value="cpp">C++</option>
        </select>
      </header>

      {/* Main Content: Split Screen */}
      <div className="flex-1 flex flex-row h-[calc(100vh-64px)]">
        
        {/* Left Panel: Problem Description */}
        <div className="w-1/3 bg-gray-900 p-6 border-r border-gray-700 overflow-y-auto">
          {problem ? (
            <>
              <h2 className="text-2xl font-bold mb-4">{problem.title}</h2>
              <span className={`inline-block px-2 py-1 text-xs font-semibold rounded mb-4 
                ${problem.difficulty === "Easy" ? "bg-green-900 text-green-300" : "bg-red-900 text-red-300"}`}>
                {problem.difficulty}
              </span>
              <p className="text-gray-300 leading-relaxed">
                Given two integers <code>a</code> and <code>b</code>, return the sum of the two integers.
              </p>
              
              <div className="mt-8">
                <h3 className="font-bold text-gray-400 mb-2">Example 1:</h3>
                <div className="bg-gray-800 p-3 rounded text-sm font-mono text-gray-300">
                  Input: a = 1, b = 2<br/>
                  Output: 3
                </div>
              </div>
            </>
          ) : (
            <p className="text-gray-500">Loading problem...</p>
          )}
        </div>

        {/* Right Panel: Code Editor & Console */}
        <div className="w-2/3 flex flex-col bg-gray-900">
          
          {/* Code Editor (Monaco) */}
          <div className="flex-1 border-b border-gray-700 relative">
             <Editor
               height="100%"
               defaultLanguage="python"
               language={language === "cpp" ? "cpp" : "python"}
               theme="vs-dark"
               value={code}
               onChange={(value) => setCode(value)}
               options={{
                 minimap: { enabled: false },
                 fontSize: 14,
                 scrollBeyondLastLine: false,
                 automaticLayout: true,
               }}
             />
             
             {/* Floating Run Button */}
             <button 
               onClick={handleSubmit}
               disabled={loading}
               className={`absolute bottom-4 right-4 px-6 py-2 rounded shadow-lg font-bold transition-colors
                 ${loading ? "bg-gray-600 cursor-not-allowed" : "bg-green-600 hover:bg-green-500 text-white"}`}
             >
               {loading ? "Running..." : "Run Code ▶"}
             </button>
          </div>

          {/* Console / Terminal Output */}
          <div className="h-48 bg-gray-900 p-4 overflow-y-auto">
            <h3 className="text-sm font-bold text-gray-500 uppercase mb-2">Console Output</h3>
            
            {output && (
              <div className={`p-3 rounded border font-mono text-sm whitespace-pre-wrap
                ${output.status === "Accepted" 
                  ? "bg-green-900/30 border-green-800 text-green-400" 
                  : "bg-red-900/30 border-red-800 text-red-400"}`}>
                
                {output.status === "Accepted" ? (
                   <>
                     <span className="font-bold text-lg">✅ Accepted</span>
                     <br/>
                     <span className="opacity-80">Passed {output.passed}/{output.total} test cases.</span>
                   </>
                ) : (
                  <>
                    <span className="font-bold text-lg">❌ {output.status}</span>
                    <br/>
                    {output.error && <span>Error: {output.error}</span>}
                    {output.expected && (
                      <div className="mt-2">
                        <span className="text-gray-400">Input: </span> {output.test_case}<br/>
                        <span className="text-gray-400">Expected: </span> {output.expected}<br/>
                        <span className="text-gray-400">Got: </span> {output.got}
                      </div>
                    )}
                    {output.docker_logs && <pre className="mt-2 text-xs text-gray-500">{output.docker_logs}</pre>}
                  </>
                )}
              </div>
            )}
            
            {!output && !loading && (
              <div className="text-gray-600 text-sm italic">
                Run your code to see results here...
              </div>
            )}
          </div>

        </div>
      </div>
    </div>
  );
}

export default App;