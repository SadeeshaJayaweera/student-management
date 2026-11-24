import { spawn } from 'child_process';
import fs from 'fs';
import path from 'path';

const SCREENSHOT_DIR = path.resolve('screenshots');
if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function waitForHttp(url, timeoutMs = 30000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    try {
      const res = await fetch(url);
      if (res.ok || res.status === 404 || res.status === 200) {
        return true;
      }
    } catch (e) {
      // ignore
    }
    await sleep(500);
  }
  throw new Error(`Timeout waiting for ${url}`);
}

async function getJwt(username, password) {
  const params = new URLSearchParams();
  params.append('username', username);
  params.append('password', password);
  const res = await fetch('http://127.0.0.1:8000/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: params.toString(),
  });
  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`Login failed for ${username}: ${res.status} ${errText}`);
  }
  const data = await res.json();
  return data.access_token;
}

async function main() {
  console.log('🚀 Starting uvicorn backend...');
  const uvicornProc = spawn(
    './venv/bin/uvicorn',
    ['backend.main:app', '--host', '127.0.0.1', '--port', '8000'],
    { stdio: 'inherit' }
  );

  let chromeProc = null;
  try {
    await waitForHttp('http://127.0.0.1:8000/docs');
    console.log('✅ Backend is responding!');

    // Fetch tokens for student, lecturer, admin
    const studentToken = await getJwt('student01', 'Student@123');
    const lecturerToken = await getJwt('kperera', 'Lecturer@123');
    const adminToken = await getJwt('admin', 'Admin@123');
    console.log('🔑 Retrieved JWT tokens for student, lecturer, and admin.');

    const profileDir = `/tmp/chrome-profile-${Date.now()}`;
    fs.mkdirSync(profileDir, { recursive: true });

    console.log('🌐 Starting headless Chrome with remote debugging...');
    chromeProc = spawn(
      '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
      [
        '--headless=new',
        '--remote-debugging-port=9222',
        `--user-data-dir=${profileDir}`,
        '--window-size=1440,900',
        '--no-sandbox',
        '--disable-gpu',
        '--hide-scrollbars',
      ],
      { stdio: 'ignore' }
    );

    await waitForHttp('http://127.0.0.1:9222/json');
    console.log('✅ Chrome remote debugging is ready!');

    const targetsRes = await fetch('http://127.0.0.1:9222/json');
    const targets = await targetsRes.json();
    const pageTarget = targets.find((t) => t.type === 'page') || targets[0];
    if (!pageTarget || !pageTarget.webSocketDebuggerUrl) {
      throw new Error('No page target with webSocketDebuggerUrl found');
    }

    console.log('Connecting to WebSocket:', pageTarget.webSocketDebuggerUrl);
    const ws = new WebSocket(pageTarget.webSocketDebuggerUrl);

    await new Promise((resolve, reject) => {
      ws.addEventListener('open', resolve);
      ws.addEventListener('error', reject);
    });

    let msgId = 1;
    function send(method, params = {}) {
      return new Promise((resolve, reject) => {
        const id = msgId++;
        const onMessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.id === id) {
              ws.removeEventListener('message', onMessage);
              if (data.error) reject(new Error(JSON.stringify(data.error)));
              else resolve(data.result);
            }
          } catch (e) {
            // ignore
          }
        };
        ws.addEventListener('message', onMessage);
        ws.send(JSON.stringify({ id, method, params }));
      });
    }

    await send('Page.enable');
    await send('Runtime.enable');
    await send('Emulation.setDeviceMetricsOverride', {
      width: 1440,
      height: 900,
      deviceScaleFactor: 2,
      mobile: false,
    });

    async function capture(pageUrl, filename, waitMs = 2500, setupFn = null) {
      console.log(`📸 Navigating to ${pageUrl} -> ${filename}...`);
      await send('Page.navigate', { url: pageUrl });
      await sleep(1500);
      if (setupFn) {
        await setupFn();
      }
      await sleep(waitMs);
      const res = await send('Page.captureScreenshot', { format: 'png' });
      const buffer = Buffer.from(res.data, 'base64');
      const outPath = path.join(SCREENSHOT_DIR, filename);
      fs.writeFileSync(outPath, buffer);
      console.log(`✅ Saved ${outPath} (${(buffer.length / 1024).toFixed(1)} KB)`);
    }

    // 1. Login Page
    await capture('http://127.0.0.1:8000/login', '01_login.png', 1500, async () => {
      await send('Runtime.evaluate', {
        expression: `localStorage.clear();`,
      });
    });

    // 2. Student Dashboard
    await capture('http://127.0.0.1:8000/dashboard', '02_student_dashboard.png', 3000, async () => {
      await send('Runtime.evaluate', {
        expression: `
          localStorage.setItem('token', ${JSON.stringify(studentToken)});
          window.location.reload();
        `,
      });
    });

    // 3. Course RAG Architecture
    await capture('http://127.0.0.1:8000/course-rag', '03_course_rag.png', 2500);

    // 4. Socratic AI Teaching Assistant
    await capture('http://127.0.0.1:8000/ai-tutor', '04_ai_teaching_assistant.png', 2500);

    // 5. MCP Tool Console
    await capture('http://127.0.0.1:8000/mcp-console', '05_mcp_console.png', 2500);

    // 6. Digital Library
    await capture('http://127.0.0.1:8000/library', '06_digital_library.png', 2500, async () => {
      await send('Runtime.evaluate', {
        expression: `
          const buttons = Array.from(document.querySelectorAll('button'));
          const physBtn = buttons.find(b => b.textContent && b.textContent.includes('Physical Library'));
          if (physBtn) physBtn.click();
        `,
      });
      await sleep(1500);
    });

    // 7. Sports & Campus Clubs
    await capture('http://127.0.0.1:8000/sports', '07_sports_and_clubs.png', 2500);

    // Switch to Lecturer
    console.log('🔄 Switching to Lecturer session for AI Grading & Quiz...');
    await send('Runtime.evaluate', {
      expression: `
        localStorage.setItem('token', ${JSON.stringify(lecturerToken)});
      `,
    });

    // 8. AI Automated Grading Assistant (Feature highlight!)
    await capture('http://127.0.0.1:8000/ai-grading', '08_ai_grading_assistant.png', 3000, async () => {
      await send('Runtime.evaluate', {
        expression: `
          localStorage.setItem('token', ${JSON.stringify(lecturerToken)});
          window.location.reload();
        `,
      });
      await sleep(2000);
      await send('Runtime.evaluate', {
        expression: `
          const buttons = Array.from(document.querySelectorAll('button'));
          const runBtn = buttons.find(b => b.textContent && b.textContent.includes('Run AI Grading'));
          if (runBtn) runBtn.click();
        `,
      });
      await sleep(2000);
    });

    // 9. AI Quiz and Question Generation
    await capture('http://127.0.0.1:8000/ai-quiz-generator', '09_ai_quiz_generator.png', 2500);

    // Switch to Admin
    console.log('🔄 Switching to Admin session for Campus Operations...');
    await send('Runtime.evaluate', {
      expression: `
        localStorage.setItem('token', ${JSON.stringify(adminToken)});
      `,
    });

    // 10. Campus Operations Command
    await capture('http://127.0.0.1:8000/campus-operations', '10_campus_operations.png', 3000, async () => {
      await send('Runtime.evaluate', {
        expression: `
          localStorage.setItem('token', ${JSON.stringify(adminToken)});
          window.location.reload();
        `,
      });
    });

    console.log('🎉 All screenshots captured successfully!');
    ws.close();
  } catch (err) {
    console.error('❌ Error during screenshot capture:', err);
  } finally {
    if (chromeProc) {
      chromeProc.kill('SIGKILL');
    }
    if (uvicornProc) {
      uvicornProc.kill('SIGKILL');
    }
  }
}

main();
