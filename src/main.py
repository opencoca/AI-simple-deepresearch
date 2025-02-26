import json, subprocess, time, threading, sys, shlex, os

def load_env(path=".env.local"):
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    os.environ[key.strip()] = value.strip().strip('"')

load_env()
API_KEY = os.getenv("API_KEY")
AI_API_URL = os.getenv("AI_API_URL")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL")
FIRECRAWL_KEY = os.getenv("FIRECRAWL_KEY")
FIRECRAWL_URL = os.getenv("FIRECRAWL_URL", "https://api.firecrawl.dev/v1/search")

class Spinner:
    def __init__(self, msg="Processing"):
        self.chars = "■◤◸◤■◥◹◥■◢◿◢■◣◺◣"
        self.msg = msg
        self.spinning = False
        self.thread = None
    def spin(self):
        while self.spinning:
            for c in self.chars:
                sys.stdout.write(f"\r{self.msg} {c}")
                sys.stdout.flush()
                time.sleep(0.1)
    def start(self, msg=None):
        if msg: self.msg = msg
        self.spinning = True
        self.thread = threading.Thread(target=self.spin)
        self.thread.start()
    def stop(self):
        self.spinning = False
        if self.thread: self.thread.join()
        sys.stdout.write("\r" + " " * (len(self.msg) + 2) + "\r")
        sys.stdout.flush()

def with_spinner(msg):
    def decorator(func):
        def wrapper(*args, **kwargs):
            s = Spinner(msg)
            s.start()
            result = func(*args, **kwargs)
            s.stop()
            return result
        return wrapper
    return decorator

@with_spinner("Calling LLM API")
def call_llm(prompt, url=AI_API_URL, key=API_KEY, model=DEFAULT_MODEL):
    payload = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}]})
    cmd = f"curl -s -X POST {url}/chat/completions -H 'Authorization: Bearer {key}' -H 'Content-Type: application/json' -d {shlex.quote(payload)}"
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return json.loads(r.stdout)["choices"][0]["message"]["content"]

@with_spinner("Performing web search")
def web_search(query):
    payload = json.dumps({"query": query, "limit": 5})
    cmd = f"curl -s -X POST {FIRECRAWL_URL} -H 'Authorization: Bearer {FIRECRAWL_KEY}' -H 'Content-Type: application/json' -d {shlex.quote(payload)}"
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    data = json.loads(r.stdout)
    results = []
    for item in data.get("data", []):
        text = item.get("title", "")
        if item.get("description"):
            text += f" – {item['description']}"
        if item.get("url"):
            text += f" ({item['url']})"
        if text:
            results.append(text)
    return results

@with_spinner("Gen Subtopics")
def gen_subtopics(topic):
    prompt = f"For the topic '{topic}', list 3-5 key subtopics that should be researched. Return only the subtopics, one per line."
    raw = call_llm(prompt)
    subs = []
    for line in raw.split("\n"):
        line = line.strip()
        if line:
            if line[0].isdigit() or line[0] in "•●-*":
                parts = line.split(" ", 1)
                if len(parts) > 1:
                    line = parts[1]
            subs.append(line)
    print(f"\nSubtopics for '{topic}':")
    for i, sub in enumerate(subs, 1):
        print(f"{i}. {sub}")
    return subs

def summarize_topic(topic, results):
    prompt = f"Provide a concise summary of these search results about '{topic}':\n\n{results}"
    return call_llm(prompt)

def research_topic(topic, depth=0, max_depth=2):
    print("  " * depth + f"Researching: {topic}")
    results = web_search(topic)
    summary = summarize_topic(topic, results)
    if depth >= max_depth:
        return {"topic": topic, "summary": summary, "subtopics": []}
    subs = gen_subtopics(topic)
    children = [research_topic(f"{topic}: {sub}", depth+1, max_depth) for sub in subs]
    return {"topic": topic, "summary": summary, "subtopics": children}

def gen_markdown(res, depth=0):
    md = f"{'#'*(depth+1)} {res['topic']}\n\n{res['summary']}\n\n"
    for sub in res['subtopics']:
        md += gen_markdown(sub, depth+1)
    return md

def valid_topic(topic):
    return topic and len(topic.split()) >= 2

def main():
    while True:
        topic = input("What would you like to research? ").strip()
        if valid_topic(topic):
            if input(f"Research '{topic}'? (y/n): ").lower().startswith('y'):
                break
        else:
            return
        print("Let's try again.")
    print(f"Starting research on: {topic}\n")
    res = research_topic(topic)
    md = gen_markdown(res)
    
    sanitized_topic = topic.replace(" ", "_")
    filename = f"recursive_research_output-{sanitized_topic}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"Results saved to '{filename}'")

if __name__ == "__main__":
    main()
