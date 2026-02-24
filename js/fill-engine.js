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

    // 1. Show Fill Specific Skeletons IMMEDIATELY
    const container = document.getElementById('quiz-container');
    container.innerHTML = Array(5).fill(UX.Skeletons.getFillSkeleton()).join('');

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

// Build a single fill card and append to parent (DocumentFragment or container)
function buildFillCard(item, index, parent) {
    const displayNum = index + 1;

    const card = document.createElement('div');
    card.className = "opacity-0 fill-card-entry bg-[#1e293b] rounded-xl border border-slate-700/50 shadow-lg overflow-hidden break-inside-avoid inline-block w-full mb-1";
    card.setAttribute('data-answered', 'false');

    const qContent = document.createElement('div');
    qContent.className = "p-4 md:p-5 flex gap-3 md:gap-4 items-baseline";

    const qNum = document.createElement('span');
    qNum.className = "font-black text-[#38bdf8] text-xl md:text-2xl min-w-[1.8rem]";
    qNum.textContent = `${displayNum}.`;

    const textContainer = document.createElement('div');
    textContainer.className = "text-white font-bold text-lg md:text-xl leading-snug tracking-wide flex-1";

    const blankId = `blank-${displayNum}`;
    let processedText = item.q.replace(/_{2,}|\.{3,}|…/g, `<span id="${blankId}" class="inline-block min-w-[100px] border-b-2 border-slate-500 text-transparent text-center px-1 transition-all font-extrabold">_______</span>`);
    textContainer.innerHTML = processedText;

    const btnContainer = document.createElement('span');
    btnContainer.className = "inline-flex flex-wrap gap-2 ml-3 align-baseline";

    const correctText = item.options[item.answer];
    let opts = item.options.map(opt => ({ text: opt, isCorrect: opt === correctText }));

    // Fisher-Yates shuffle for proper uniform distribution
    opts = UX.fisherYatesShuffle(opts);

    opts.forEach(optObj => {
        const btn = document.createElement('button');
        btn.className = "px-3 py-1 rounded-full border border-slate-600 bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-sm transition-all duration-200 active:scale-95 shadow-sm align-middle";
        btn.textContent = optObj.text;
        btn.onclick = () => handleAnswer(btn, optObj, blankId, btnContainer, card);
        btnContainer.appendChild(btn);
    });

    textContainer.appendChild(btnContainer);
    qContent.appendChild(qNum);
    qContent.appendChild(textContainer);
    card.appendChild(qContent);
    parent.appendChild(card);
}

function render() {
    const container = document.getElementById('quiz-container');
    container.innerHTML = '';

    // Progressive rendering: first 5 cards immediate, rest on idle
    UX.renderProgressive(displayQuestions, buildFillCard, container, 5);

    // TRIGGER STAGGER ANIMATION after a microtask (so DOM is ready)
    requestAnimationFrame(() => {
        UX.staggerElements('.fill-card-entry', 30);
    });
}

function handleAnswer(btn, optObj, blankId, container, card) {
    if (card.getAttribute('data-answered') === 'true') return;

    // Visual feedback immediately
    btn.style.transform = "scale(0.95)";

    if (optObj.isCorrect) {
        // CORRECT: Instant
        Sound.playCorrect();
        Effects.triggerConfetti();

        btn.className = "px-3 py-1 rounded-full border border-emerald-500 bg-emerald-500/20 text-emerald-400 font-bold text-sm shadow-[0_0_15px_rgba(16,185,129,0.4)] animate-pop pointer-events-none align-middle transition-all";

        const blank = document.getElementById(blankId);
        if (blank) {
            blank.textContent = optObj.text;
            blank.classList.remove('text-transparent', 'border-slate-500');
            blank.classList.add('text-[#34d399]', 'border-[#34d399]');
        }
        card.setAttribute('data-answered', 'true');

        // Disable siblings
        const siblings = container.querySelectorAll('button');
        siblings.forEach(b => {
            if (b !== btn) {
                b.disabled = true;
                b.classList.add('opacity-50', 'cursor-not-allowed');
            }
        });

    } else {
        // WRONG: Slight delay
        setTimeout(() => {
            Sound.playWrong();
            btn.className = "px-3 py-1 rounded-full border border-red-500 bg-red-500/20 text-red-400 font-semibold text-sm animate-shake align-middle cursor-not-allowed";
            btn.disabled = true;
            btn.style.transform = "scale(1)";
        }, 150);
    }
}

init();