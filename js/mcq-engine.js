import { Sound, Effects, injectHeader, injectFooter, injectMenu, getParams, discoverSetsFromConfig, discoverSetsFallback, UX, initPrintProtection } from './ui.js';

let allQuestions = [];
let displayQuestions = [];
let currentSetId = 1;
let availableSets = [1];

async function init() {
    // 0. Init Print Protection
    initPrintProtection();

    const { topic, level, set } = getParams();
    currentSetId = set;

    // 1. Show MCQ Specific Skeletons IMMEDIATELY
    const container = document.getElementById('quiz-container');
    container.innerHTML = Array(5).fill(UX.Skeletons.getMCQSkeleton()).join('');

    // 2. PARALLEL LOAD: Config + Data fetched simultaneously (saves 200-400ms)
    const configPath = `../data/${topic}/${level}/config.js`;
    const dataUrl = `../data/${topic}/${level}/set${set}.json`;

    const [config, dataResult] = await Promise.all([
        import(configPath).then(m => m.default).catch(() => ({})),
        fetch(dataUrl).then(res => {
            if (!res.ok) throw new Error("Set not found");
            return res.json();
        }).catch(e => ({ error: true, message: e.message, url: dataUrl }))
    ]);

    // 3. Inject Header (uses config, no network)
    injectHeader(
        config.headerTitle || topic.replace(/-/g, ' '),
        `${config.headerSubtitlePrefix || "By Chiranjibi Sir"} • ${level.toUpperCase()} • SET ${set}`
    );

    injectFooter();

    // 4. Discover Sets INSTANTLY from config (zero network calls)
    const configSets = discoverSetsFromConfig(config);
    availableSets = configSets || await discoverSetsFallback(topic, level);

    // 5. Handle Data Result
    if (dataResult && dataResult.error) {
        container.innerHTML = `<div class="text-center py-20 text-slate-500 font-bold">Failed to load: ${dataResult.url}<br>${dataResult.message}</div>`;
        setupMenu();
        return;
    }

    allQuestions = dataResult;
    displayQuestions = [...allQuestions];

    // 6. Prefetch next set in background
    UX.prefetchNextSet(topic, level, set);

    setupMenu();
    render();
}

function setupMenu() {
    injectMenu(
        currentSetId,
        availableSets,
        (newSet) => {
            const { topic, level } = getParams();
            window.location.href = `?subject=${topic}&level=${level}&set=${newSet}`;
        },
        (filterType) => {
            if (filterType === 'odd') displayQuestions = allQuestions.filter((_, i) => (i + 1) % 2 !== 0);
            if (filterType === 'even') displayQuestions = allQuestions.filter((_, i) => (i + 1) % 2 === 0);
            render();
            closeMenu();
        },
        (count) => {
            const c = parseInt(count) || 10;
            const shuffled = UX.fisherYatesShuffle(allQuestions);
            displayQuestions = shuffled.slice(0, c);
            render();
            closeMenu();
        }
    );
}

function closeMenu() {
    document.getElementById('teacher-menu').classList.remove('open');
}

// Build a single MCQ card and append to parent (DocumentFragment or container)
function buildMCQCard(item, index, parent) {
    const displayNum = index + 1;

    // Shuffle Options with Fisher-Yates
    const correctText = item.options[item.answer];
    let opts = item.options.map((opt, i) => ({ text: opt, originalIndex: i }));
    opts = UX.fisherYatesShuffle(opts);
    const newAnswerIndex = opts.findIndex(o => o.text === correctText);

    const card = document.createElement('div');
    card.className = "opacity-0 quiz-card-entry bg-[#1e293b] rounded-xl md:rounded-2xl shadow-2xl border-2 border-slate-700 overflow-hidden break-inside-avoid mb-4";
    card.setAttribute('data-answered', 'false');

    const header = document.createElement('div');
    header.className = "bg-[#0f172a] px-4 py-3 md:px-6 md:py-4 border-b border-slate-700 flex gap-3 md:gap-4 items-start";
    header.innerHTML = `
        <span class="font-black text-blue-400 text-lg md:text-xl whitespace-nowrap mt-0.5 bg-blue-900/30 px-3 py-1 rounded-lg border border-blue-800 shadow-[0_0_10px_rgba(30,58,138,0.5)]">Q${displayNum}</span>
        <p class="text-white font-bold text-lg md:text-xl leading-relaxed tracking-wide pt-0.5">${item.q.replace(/_{2,}/g, '__________')}</p>
    `;

    const optsDiv = document.createElement('div');
    optsDiv.className = "p-4 md:p-6 grid grid-cols-1 md:grid-cols-2 gap-3 md:gap-4";

    const letters = ['A', 'B', 'C', 'D'];
    opts.forEach((optObj, i) => {
        const btn = document.createElement('button');
        btn.className = "option-btn w-full text-left px-4 py-3 md:px-5 md:py-4 rounded-lg md:rounded-xl border-2 border-slate-600 text-slate-100 font-bold text-base md:text-lg bg-slate-800 hover:bg-slate-700 hover:border-slate-500 focus:outline-none relative overflow-hidden group flex items-center shadow-lg transition-all transform active:scale-95";

        btn.innerHTML = `
            <span class="badge-default inline-flex items-center justify-center w-8 h-8 rounded-lg text-sm font-black mr-3 transition-colors shrink-0 border border-slate-500 bg-slate-700 text-slate-400 group-hover:border-slate-400">${letters[i]}</span>
            <span class="flex-1">${optObj.text}</span>
        `;

        btn.onclick = () => handleAnswer(btn, i, newAnswerIndex, optsDiv, card);
        optsDiv.appendChild(btn);
    });

    card.appendChild(header);
    card.appendChild(optsDiv);
    parent.appendChild(card);
}

function render() {
    const container = document.getElementById('quiz-container');
    container.innerHTML = '';

    if (displayQuestions.length === 0) {
        container.innerHTML = `<div class="text-center py-20 text-slate-500">No questions found.</div>`;
        return;
    }

    // Progressive rendering: first 5 cards immediate, rest on idle
    UX.renderProgressive(displayQuestions, buildMCQCard, container, 5);

    // TRIGGER STAGGER ANIMATION after a microtask (so DOM is ready)
    requestAnimationFrame(() => {
        UX.staggerElements('.quiz-card-entry', 30);
    });
}

function handleAnswer(btn, index, correctIndex, container, card) {
    const badge = btn.querySelector('span');

    // 1. INSTANT FEEDBACK (Optimistic)
    btn.style.transform = "scale(0.98)";

    // Remove existing animations (using class toggle instead of forced reflow)
    if (btn.classList.contains('animate-shake')) {
        btn.classList.remove('animate-shake');
        // Use requestAnimationFrame instead of forced reflow for animation reset
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                processAnswer(btn, index, correctIndex, badge, container, card);
            });
        });
    } else {
        processAnswer(btn, index, correctIndex, badge, container, card);
    }
}

function processAnswer(btn, index, correctIndex, badge, container, card) {
    if (index === correctIndex) {
        // CORRECT: Instant Gratification
        Sound.playCorrect();
        Effects.triggerConfetti();

        btn.className = "option-btn w-full text-left px-4 py-3 md:px-5 md:py-4 rounded-lg md:rounded-xl border-2 border-[#22c55e] bg-[#16a34a] text-white font-bold text-base md:text-lg shadow-[0_0_15px_rgba(34,197,94,0.4)] flex items-center opacity-100 transition-all duration-200";
        if (badge) badge.className = "inline-flex items-center justify-center w-8 h-8 rounded-lg text-sm font-black mr-3 shrink-0 border border-white text-white bg-transparent";

        btn.style.transform = "scale(1)";
        card.setAttribute('data-answered', 'true');

    } else {
        // WRONG: Psychological Delay (Tension)
        setTimeout(() => {
            Sound.playWrong();
            btn.className = "option-btn w-full text-left px-4 py-3 md:px-5 md:py-4 rounded-lg md:rounded-xl border-2 border-[#ef4444] bg-[#dc2626] text-white font-bold text-base md:text-lg shadow-[0_0_15px_rgba(239,68,68,0.4)] animate-shake flex items-center opacity-100";
            if (badge) badge.className = "inline-flex items-center justify-center w-8 h-8 rounded-lg text-sm font-black mr-3 shrink-0 border border-white text-white bg-transparent";
            btn.style.transform = "scale(1)";
        }, 150);
    }
}

init();