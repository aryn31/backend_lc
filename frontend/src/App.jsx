import { useState, useEffect } from "react";
import axios from "axios";
import Editor from "@monaco-editor/react";

function App() {
  const [code, setCode] = useState("# Write your Python code here\ndef add(a, b):\n    return a + b");
  const [output, setOutput] = useState(null);
  const [loading, setLoading] = useState(false);
  const [problem, setProblem] = useState(null);
  const [language, setLanguage] = useState("python");
  
  // NEW STATE: For the History Tab
  const [activeTab, setActiveTab] = useState("description"); // "description" or "history"
  const [history, setHistory] = useState([]);

  // Fetch the problem details when the page loads
  useEffect(() => {
    async function fetchProblem() {
      try {
        const res = await axios.get("http://127.0.0.1:8000/problems");
        if (res.data.length > 0) {
          setProblem(res.data[0]); 
          fetchHistory(res.data[0].id); // Fetch history immediately
        }
      } catch (err) {
        console.error("Backend not running?", err);
      }
    }
    fetchProblem();
  }, []);

  // NEW FUNCTION: Fetch the submission history
  const fetchHistory = async (problemId) => {
    try {
      const res = await axios.get(`http://127.0.0.1:8000/problems/${problemId}/submissions`);
      setHistory(res.data);
    } catch (err) {
      console.error("Could not fetch history");
    }
  };

  const handleSubmit = async () => {
    setLoading(true);
    setOutput(null);
    try {
      const payload = {
        problem_id: problem.id,
        language: language,
        code: code,
      };
      
      const res = await axios.post("http://127.0.0.1:8000/submit", payload);
      setOutput(res.data);
      
      // NEW: Refresh the history silently in the background after submitting!
      fetchHistory(problem.id); 
      
    } catch (err) {
      setOutput({ status: "System Error", details: "Could not connect to server." });
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
        
        {/* Left Panel: Description OR History */}
        <div className="w-1/3 bg-gray-900 flex flex-col border-r border-gray-700">
          
          {/* Tabs UI */}
          <div className="flex border-b border-gray-700 bg-gray-800">
            <button 
              className={`flex-1 py-3 font-semibold text-sm transition-colors ${activeTab === "description" ? "text-white border-b-2 border-blue-500" : "text-gray-400 hover:text-gray-200"}`}
              onClick={() => setActiveTab("description")}
            >
              Description
            </button>
            <button 
              className={`flex-1 py-3 font-semibold text-sm transition-colors ${activeTab === "history" ? "text-white border-b-2 border-blue-500" : "text-gray-400 hover:text-gray-200"}`}
              onClick={() => setActiveTab("history")}
            >
              Submissions ({history.length})
            </button>
          </div>

          {/* Tab Content */}
          <div className="p-6 overflow-y-auto flex-1">
            {activeTab === "description" ? (
              // --- DESCRIPTION TAB ---
              problem ? (
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
              )
            ) : (
              // --- HISTORY TAB ---
              <div className="flex flex-col gap-3">
                {history.length === 0 ? (
                  <p className="text-gray-500 italic text-center mt-10">No submissions yet.</p>
                ) : (
                  history.map((sub) => (
                    <div key={sub.id} className="bg-gray-800 p-3 rounded border border-gray-700 flex justify-between items-center cursor-pointer hover:bg-gray-750 transition-colors"
                         onClick={() => setCode(sub.code)}> {/* Clicking loads past code! */}
                      <span className={`font-bold text-sm ${sub.status === "Accepted" ? "text-green-400" : "text-red-400"}`}>
                        {sub.status}
                      </span>
                      <span className="text-xs text-gray-500 font-mono">ID: #{sub.id}</span>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right Panel: Code Editor & Console */}
        <div className="w-2/3 flex flex-col bg-gray-900">
          
          <div className="flex-1 border-b border-gray-700 relative">
             <Editor
               height="100%"
               defaultLanguage="python"
               language={language === "cpp" ? "cpp" : "python"}
               theme="vs-dark"
               value={code}
               onChange={(value) => setCode(value)}
               options={{ minimap: { enabled: false }, fontSize: 14, scrollBeyondLastLine: false, automaticLayout: true }}
             />
             
             <button 
               onClick={handleSubmit}
               disabled={loading}
               className={`absolute bottom-4 right-4 px-6 py-2 rounded shadow-lg font-bold transition-colors
                 ${loading ? "bg-gray-600 cursor-not-allowed" : "bg-green-600 hover:bg-green-500 text-white"}`}
             >
               {loading ? "Running..." : "Run Code ▶"}
             </button>
          </div>

          <div className="h-48 bg-gray-900 p-4 overflow-y-auto">
            <h3 className="text-sm font-bold text-gray-500 uppercase mb-2">Console Output</h3>
            
            {output && (
              <div className={`p-3 rounded border font-mono text-sm whitespace-pre-wrap
                ${output.status === "Accepted" ? "bg-green-900/30 border-green-800 text-green-400" : "bg-red-900/30 border-red-800 text-red-400"}`}>
                
                {output.status === "Accepted" ? (
                   <>
                     <span className="font-bold text-lg">✅ Accepted</span><br/>
                     <span className="opacity-80">Passed {output.passed}/{output.total} test cases.</span>
                   </>
                ) : (
                  <>
                    <span className="font-bold text-lg">❌ {output.status}</span><br/>
                    {output.details && <div className="mt-2 text-yellow-400 font-mono bg-black p-2 rounded">Backend Crash: {output.details}</div>}
                    {output.error && <span>Error: {output.error}</span>}
                    {output.expected !== undefined && (
                      <div className="mt-2 bg-gray-950 p-2 rounded border border-red-900/50">
                        <span className="text-gray-400">Test Case: </span> #{output.test_case}<br/>
                        <span className="text-gray-400">Input: </span> 
                        <span className="text-blue-300 font-mono">
                          {typeof output.input === 'string' ? output.input : JSON.stringify(output.input)}
                        </span><br/>
                        <span className="text-gray-400">Expected: </span> 
                        <span className="text-green-400 font-mono">{JSON.stringify(output.expected)}</span><br/>
                        <span className="text-gray-400">Got: </span> 
                        <span className="text-red-400 font-mono">{JSON.stringify(output.got)}</span>
                      </div>
                    )}
                    {output.docker_logs && <pre className="mt-2 text-xs text-gray-500">{output.docker_logs}</pre>}
                  </>
                )}
              </div>
            )}
            
            {!output && !loading && <div className="text-gray-600 text-sm italic">Run your code to see results here...</div>}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;