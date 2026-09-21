(()=>{const modules={"portal/appearance.js":function(capsule,published,resolve){/* Validated portal appearance. Deliverable artwork keeps its own recipe. */
(() => {
  const key = "yeshan-portal-appearance-v1",
    media =
      typeof matchMedia === "function"
        ? matchMedia("(prefers-color-scheme: dark)")
        : { matches: false };
  const defaults = {
    theme: "dark",
    panel: "frosted",
    card: "plain",
    accent: "auto",
    background: "auto",
    foreground: "auto",
    contrast: 50,
    font: "interface",
    textSize: 16,
    lineHeight: 1.7,
    tracking: 0,
    weight: 400,
    padding: 20,
    duration: 380,
    densityMode: "comfortable",
    densityPresets: {
      compact: {
        padding: 16,
        rowHeight: 36,
        cardRatio: 1.8,
        lineHeight: 1.5,
        tracking: 0,
        textSize: 14,
        gap: 8,
      },
      comfortable: {
        padding: 20,
        rowHeight: 44,
        cardRatio: 1.5,
        lineHeight: 1.7,
        tracking: 0,
        textSize: 16,
        gap: 20,
      },
      editorial: {
        padding: 28,
        rowHeight: 52,
        cardRatio: 1.1,
        lineHeight: 1.9,
        tracking: 0.015,
        textSize: 18,
        gap: 28,
      },
    },
    rowHeight: 44,
    cardRatio: 1.5,
    previewBackdrop: "gradient",
    buttonStyle: "solid",
    applications: { version: 1, site: {}, workbench: {}, reference: {} },
    palettes: Object.fromEntries(
      ["dark", "light"].map((mode) => [
        mode,
        {
          accent: "auto",
          background: "auto",
          foreground: "auto",
          panel: "auto",
          muted: "auto",
          border: "auto",
          hover: "auto",
          active: "auto",
          focus: "auto",
          onAccent: "auto",
          inputBackground: "auto",
          inputForeground: "auto",
          inputBorder: "auto",
          inputOpacity: 90,
          borderOpacity: 100,
          inputBorderOpacity: 100,
          navBackground: "auto",
          navSelected: "auto",
          navForeground: "auto",
          navActiveForeground: "auto",
          navOpacity: 86,
          controlBackground: "auto",
          controlHover: "auto",
          controlForeground: "auto",
          controlOpacity: 100,
          surfaceBackgroundMode: "solid",
          surfaceGradient: {
            backgroundMode: "linear",
            angle: 130,
            blend: 70,
            centerX: 50,
            centerY: 50,
            weights: null,
            positions: [0, 50, 100],
            anchors: [
              { x: 10, y: 75 },
              { x: 78, y: 70 },
              { x: 50, y: 50 },
            ],
            stops:
              mode === "dark"
                ? ["#242b27", "#333b30", "#25363d"]
                : ["#f5ede0", "#d6e7df", "#dfe5f5"],
          },
          backgroundMode: "solid",
          angle: 130,
          positions: [0, 50, 100],
          weights: null,
          centerX: 20,
          centerY: 20,
          blend: 70,
          anchors: [
            { x: 10, y: 75 },
            { x: 78, y: 70 },
            { x: 20, y: 20 },
          ],
          accentMode: "solid",
          accentGradient: {
            backgroundMode: "linear",
            angle: 120,
            positions: [0, 50, 100],
            weights: null,
            stops: ["#82b895", "#84b6d7", "#b496d4"],
            centerX: 50,
            centerY: 50,
            blend: 70,
            anchors: [
              { x: 10, y: 75 },
              { x: 78, y: 70 },
              { x: 50, y: 50 },
            ],
          },
          stops:
            mode === "dark"
              ? ["#111923", "#364638", "#3d2e49"]
              : ["#f5ede0", "#d6e7df", "#dfe5f5"],
        },
      ]),
    ),
    surfaces: Object.fromEntries(
      ["panel", "card"].map((role) => [
        role,
        {
          plain: { opacity: 100, blur: 0, refraction: 0, shadow: 0, border: 1 },
          frosted: {
            opacity: 82,
            blur: 20,
            refraction: 0,
            shadow: 12,
            border: 1,
          },
          clear: {
            opacity: 40,
            blur: 2,
            refraction: 48,
            shadow: 16,
            border: 1,
          },
        },
      ]),
    ),
  };
  const clamp = (v, lo, hi, fallback) =>
    typeof v === "number" && Number.isFinite(v)
      ? Math.min(hi, Math.max(lo, v))
      : fallback;
  const one = (v, values, fallback) => (values.includes(v) ? v : fallback);
  function normalizeGradient(raw, fallback, allowSolid = false) {
    const supplied =
      Array.isArray(raw.stops) &&
      raw.stops.length >= 1 &&
      raw.stops.length <= 24;
    const stops = supplied
      ? raw.stops.map((c, i) =>
          /^#[\da-f]{6}$/i.test(c)
            ? c
            : fallback.stops[i % fallback.stops.length],
        )
      : [...fallback.stops];
    const n = stops.length;
    const weights =
      Array.isArray(raw.weights) &&
      raw.weights.length === n &&
      raw.weights.every(
        (v) => typeof v === "number" && Number.isFinite(v) && v >= 0,
      ) &&
      raw.weights.some((v) => v > 0)
        ? raw.weights.map(
            (v) => (v / raw.weights.reduce((a, b) => a + b, 0)) * 100,
          )
        : null;
    return {
      backgroundMode: one(
        raw.backgroundMode,
        allowSolid
          ? ["solid", "linear", "radial", "mesh"]
          : ["linear", "radial", "mesh"],
        allowSolid ? "solid" : "linear",
      ),
      angle: clamp(raw.angle, 0, 360, fallback.angle),
      blend: clamp(raw.blend, 0, 100, fallback.blend),
      centerX: clamp(raw.centerX, 0, 100, fallback.centerX),
      centerY: clamp(raw.centerY, 0, 100, fallback.centerY),
      stops,
      weights,
      positions: stops.map((c, i) =>
        clamp(raw.positions?.[i], 0, 100, n === 1 ? 50 : (i / (n - 1)) * 100),
      ),
      anchors: stops.map((c, i) => ({
        x: clamp(
          raw.anchors?.[i]?.x,
          0,
          100,
          fallback.anchors[i]?.x ?? ((i + 1) / (n + 1)) * 100,
        ),
        y: clamp(raw.anchors?.[i]?.y, 0, 100, fallback.anchors[i]?.y ?? 50),
      })),
    };
  }
  function normalize(value = {}) {
    const p = structuredClone(defaults);
    if (!value || typeof value !== "object") return p;
    p.theme = one(value.theme, ["light", "dark", "system"], p.theme);
    for (const role of ["panel", "card"]) {
      p[role] = one(value[role], ["plain", "frosted", "clear"], p[role]);
      for (const material of ["plain", "frosted", "clear"])
        for (const [k, lo, hi] of [
          ["opacity", 0, 100],
          ["blur", 0, 40],
          ["refraction", 0, 100],
          ["shadow", 0, 32],
          ["border", 0, 3],
        ])
          p.surfaces[role][material][k] = clamp(
            value.surfaces?.[role]?.[material]?.[k],
            lo,
            hi,
            p.surfaces[role][material][k],
          );
    }
    p.buttonStyle = one(
      value.buttonStyle,
      ["solid", "outline", "soft", "metal", "beam"],
      "solid",
    );
    for (const target of ["site", "workbench", "reference"])
      for (const id of ["metal", "gooey", "orb", "beam"]) {
        const v = value.applications?.[target]?.[id];
        if (!v || typeof v !== "object") continue;
        p.applications[target][id] =
          id === "metal"
            ? {
                preset: one(
                  v.preset,
                  ["chromatic", "silver", "gold"],
                  "silver",
                ),
                strength: clamp(v.strength, 0, 1, 1),
              }
            : id === "beam"
              ? { size: one(v.size, ["md", "sm", "line"], "md") }
              : id === "gooey"
                ? { blur: clamp(v.blur, 2, 10, 6) }
                : {
                    state: one(
                      v.state,
                      [
                        "working",
                        "searching",
                        "solving",
                        "listening",
                        "connecting",
                        "weaving",
                        "composing",
                        "breathing",
                        "shaping",
                      ],
                      "searching",
                    ),
                  };
      }
    const chosen =
      p.theme === "system" ? (media.matches ? "dark" : "light") : p.theme;
    for (const mode of ["light", "dark"]) {
      const raw =
        value.palettes?.[mode] ||
        (!value.palettes && mode === chosen ? value : {});
      const pal = p.palettes[mode];
      for (const k of [
        "accent",
        "background",
        "foreground",
        "panel",
        "muted",
        "border",
        "hover",
        "active",
        "focus",
        "onAccent",
        "inputBackground",
        "inputForeground",
        "inputBorder",
        "navBackground",
        "navSelected",
        "navForeground",
        "navActiveForeground",
        "controlBackground",
        "controlHover",
        "controlForeground",
      ])
        pal[k] = /^#[\da-f]{6}$/i.test(raw[k]) ? raw[k] : "auto";
      pal.inputOpacity = clamp(raw.inputOpacity, 0, 100, 90);
      for (const k of ["borderOpacity", "inputBorderOpacity", "controlOpacity"])
        pal[k] = clamp(raw[k], 0, 100, 100);
      pal.navOpacity = clamp(raw.navOpacity, 0, 100, 86);
      pal.surfaceBackgroundMode = one(
        raw.surfaceBackgroundMode,
        ["solid", "gradient"],
        "solid",
      );
      pal.surfaceGradient = normalizeGradient(
        raw.surfaceGradient || {},
        pal.surfaceGradient,
      );
      Object.assign(pal, normalizeGradient(raw, pal, true));
      pal.accentMode = one(raw.accentMode, ["solid", "gradient"], "solid");
      pal.accentGradient = normalizeGradient(
        raw.accentGradient || {},
        pal.accentGradient,
      );
    }
    for (const k of ["accent", "background", "foreground"])
      p[k] = p.palettes[chosen][k];
    p.previewBackdrop = one(
      value.previewBackdrop,
      ["gradient", "page", "solid"],
      "gradient",
    );
    p.font = one(value.font, ["interface", "system", "editorial"], p.font);
    for (const [k, lo, hi] of [
      ["contrast", 0, 100],
      ["textSize", 14, 20],
      ["lineHeight", 1.4, 2],
      ["tracking", -0.02, 0.08],
      ["weight", 300, 600],
      ["padding", 12, 32],
      ["duration", 0, 700],
      ["rowHeight", 32, 64],
      ["cardRatio", 0.8, 2.4],
    ])
      p[k] = clamp(value[k], lo, hi, p[k]);
    p.densityMode = one(
      value.densityMode,
      ["compact", "comfortable", "editorial"],
      "comfortable",
    );
    for (const mode of Object.keys(p.densityPresets))
      for (const [k, lo, hi] of [
        ["padding", 12, 32],
        ["rowHeight", 32, 64],
        ["cardRatio", 0.8, 2.4],
        ["lineHeight", 1.4, 2],
        ["tracking", -0.02, 0.08],
        ["textSize", 14, 20],
        ["gap", 8, 32],
      ])
        p.densityPresets[mode][k] = clamp(
          value.densityPresets?.[mode]?.[k],
          lo,
          hi,
          p.densityPresets[mode][k],
        );
    return p;
  }
  // The native plugin imports validation and gradient code without touching host preferences.
  if (typeof capsule === "object" && capsule.published) {
    capsule.published = { defaults, normalize, gradient, gradientStops };
    return;
  }
  const rootExport = () =>
    document.documentElement.hasAttribute("data-recipe-export") ||
    document.documentElement.hasAttribute("data-portal-embedded");
  let prefs;
  try {
    let saved = JSON.parse(
      rootExport() ? "{}" : localStorage.getItem(key) || "{}",
    );
    if (window.YeshanEmbed) saved = YeshanEmbed.appearance.get();
    else if (!rootExport()) {
      try {
        const draft = JSON.parse(
          sessionStorage.getItem("yeshan-recipe-edit-v2") || "null",
        );
        if (draft?.baseline?.appearance && draft.current?.appearance)
          saved = draft.current.appearance;
      } catch {}
    }
    if (!saved.applications && !rootExport()) {
      try {
        saved.applications = JSON.parse(
          localStorage.getItem("yeshan-library-applications-v1") || "null",
        );
      } catch {}
    }
    if (!saved.buttonStyle && saved.applications?.site?.metal)
      saved.buttonStyle = "metal";
    prefs = normalize(saved);
  } catch {
    prefs = normalize();
  }
  const root = document.documentElement,
    glass = new Map();
  const effective = () =>
    prefs.theme === "system" ? (media.matches ? "dark" : "light") : prefs.theme;
  const panelSelector =
    ".p-sidebar,.p-settings-dialog,.p-search-dialog,.delivery-editor,.np-live-panel,.np-live-editor,.recipe-popover,.p-recipe-dialog,.wb-drawer,.recipe-edit-bar,.yc-candidate-popover";
  const cardSelector =
    ".ys-card,.ws-card,.p-component-card,.p-template-card,.library-card,.id-specimen,.qp-project-row,.wb-project,.wb-task,.ytb-sample,.yc-role-field";
  let frame;
  function syncSurfaces() {
    frame = null;
    if (!document.body) return;
    for (const [node, view] of glass)
      if (!node.isConnected) {
        view.destroy();
        glass.delete(node);
      }
    document
      .querySelectorAll(panelSelector + "," + cardSelector)
      .forEach((node) => {
        if (node.closest(".ys-token-preview[data-token-theme]")) return;
        const role =
          node.dataset.recipeRole ||
          (node.matches(panelSelector) ? "panel" : "card");
        node.dataset.styleId = node.matches(".wb-drawer")
          ? "S04"
          : role === "panel"
            ? "S01"
            : "S02";
        if (node.matches(".library-card")) {
          const badge = node.querySelector(".recipe-style-label"),
            names = { plain: "实色", frosted: "毛玻璃", clear: "透明玻璃" };
          if (badge && node.classList.contains("library-icon-card")) {
            badge.textContent = node.dataset.catalogNumber;
          } else if (badge) {
            const text =
              (node.dataset.catalogNumber ||
                node.dataset.componentId ||
                "组件") +
              (node.dataset.beui ? " · " + node.dataset.beui : "") +
              " · S02 内容卡片 · " +
              names[prefs.card];
            if (badge.textContent !== text) badge.textContent = text;
          }
        }
        const material = ["plain", "frosted", "clear"].includes(
          node.dataset.material,
        )
          ? node.dataset.material
          : prefs[role];
        const p = prefs.surfaces[role][material];
        node.dataset.recipeSurface = material;
        for (const [name, value] of Object.entries({
          opacity: p.opacity + "%",
          blur: p.blur + "px",
          shadow: p.shadow + "px",
          border: p.border + "px",
        }))
          node.style.setProperty("--recipe-surface-" + name, value);
        if (material === "clear" && window.YeshanLiquidGlass) {
          if (!glass.has(node))
            glass.set(node, YeshanLiquidGlass.mount(node, { decorate: false }));
          glass.get(node).update({
            strength: p.refraction,
            blur: p.blur,
            tint: p.opacity / 100,
          });
        } else if (glass.has(node)) {
          glass.get(node).destroy();
          glass.delete(node);
        }
      });
  }
  const schedule = () => {
    if (!frame) frame = requestAnimationFrame(syncSurfaces);
  };
  const fonts = {
    interface:
      "Mluvka,'Helvetica Neue',-apple-system,BlinkMacSystemFont,'PingFang SC',sans-serif",
    system:
      "-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC',sans-serif",
    editorial: "'Songti SC','Noto Serif CJK SC',Georgia,serif",
  };
  function gradientStops(p) {
    if (p.weights?.length === p.stops.length && p.backgroundMode === "linear") {
      const sum = p.weights.reduce((a, b) => a + b, 0) || 1,
        weights = p.weights.map((w) => (w / sum) * 100),
        out = [];
      let cursor = 0;
      weights.forEach((w, i) => {
        const start = cursor;
        cursor += w;
        if (w <= 0) return;
        const before = i
          ? (Math.min(weights[i - 1], w) * (p.blend ?? 70)) / 200
          : 0;
        const after =
          i < weights.length - 1
            ? (Math.min(weights[i + 1], w) * (p.blend ?? 70)) / 200
            : 0;
        out.push(
          { c: p.stops[i], pos: start + before },
          { c: p.stops[i], pos: cursor - after },
        );
      });
      return out.map((s) => ({ ...s, pos: Math.max(0, Math.min(100, s.pos)) }));
    }
    const points = p.stops
      .map((c, i) => ({
        c,
        pos: p.positions?.[i] ?? (i / Math.max(1, p.stops.length - 1)) * 100,
      }))
      .sort((a, b) => a.pos - b.pos);
    if (points.length < 2) return points;
    const softness = Math.max(0, Math.min(1, (p.blend ?? 70) / 100));
    const out = [points[0]];
    for (let i = 0; i < points.length - 1; i++) {
      const a = points[i],
        b = points[i + 1],
        middle = (a.pos + b.pos) / 2,
        half = ((b.pos - a.pos) * softness) / 2;
      out.push({ c: a.c, pos: middle - half }, { c: b.c, pos: middle + half });
    }
    out.push(points.at(-1));
    return out;
  }
  function gradient(p = prefs.palettes[effective()]) {
    if (p.backgroundMode === "solid") return "none";
    const stops = gradientStops(p)
      .map((s) => s.c + " " + s.pos + "%")
      .join(",");
    if (p.backgroundMode === "mesh") {
      const anchors = p.anchors || [
        { x: 10, y: 75 },
        { x: 78, y: 70 },
        { x: p.centerX ?? 20, y: p.centerY ?? 20 },
      ];
      return p.stops
        .map(
          (c, i) =>
            `radial-gradient(ellipse at ${anchors[i].x}% ${anchors[i].y}%,${c},${c}00 ${p.blend ?? 70}%)`,
        )
        .reverse()
        .concat(`linear-gradient(${p.stops[0]},${p.stops[0]})`)
        .join(",");
    }
    return p.backgroundMode === "linear"
      ? `linear-gradient(${p.angle}deg,${stops})`
      : `radial-gradient(ellipse at ${p.centerX ?? 20}% ${p.centerY ?? 20}%,${stops})`;
  }
  function apply(save = false) {
    const palette = prefs.palettes[effective()];
    for (const k of ["accent", "background", "foreground"])
      prefs[k] = palette[k];
    root.dataset.portalTheme = effective();
    root.dataset.panelMaterial = prefs.panel;
    root.dataset.cardMaterial = prefs.card;
    root.dataset.buttonStyle = prefs.buttonStyle;
    root.dataset.recipeMotion = prefs.duration === 0 ? "none" : "on";
    root.style.colorScheme = effective();
    root.style.setProperty("--ys-font", fonts[prefs.font]);
    const values = {
      "--recipe-font-size": prefs.textSize + "px",
      "--recipe-font-scale": prefs.textSize / 16,
      "--recipe-line-height": prefs.lineHeight,
      "--recipe-tracking": prefs.tracking + "em",
      "--recipe-weight": prefs.weight,
      "--recipe-padding": prefs.padding + "px",
      "--ys-duration": prefs.duration + "ms",
      "--island-duration": prefs.duration + "ms",
      "--recipe-duration": prefs.duration + "ms",
      "--recipe-row-height": prefs.rowHeight + "px",
      "--recipe-card-ratio": prefs.cardRatio,
      "--recipe-background-image": gradient(),
      "--recipe-preview-background":
        prefs.previewBackdrop === "solid"
          ? "var(--ys-canvas)"
          : prefs.previewBackdrop === "page"
            ? gradient() === "none"
              ? "var(--ys-canvas)"
              : gradient()
            : gradient({
                ...palette,
                backgroundMode:
                  palette.backgroundMode === "solid"
                    ? "linear"
                    : palette.backgroundMode,
              }),
    };
    for (const role of ["panel", "card"]) {
      const p = prefs.surfaces[role][prefs[role]];
      values["--portal-" + role] =
        `color-mix(in srgb,var(--ys-panel) ${p.opacity}%,transparent)`;
      values["--portal-" + role + "-blur"] =
        prefs[role] === "plain" ? "none" : `blur(${p.blur}px)`;
    }
    const dark = effective() === "dark",
      c = prefs.contrast;
    if (prefs.accent !== "auto") {
      values["--ys-accent"] = prefs.accent;
      values["--ys-focus"] = prefs.accent;
    } else {
      root.style.removeProperty("--ys-accent");
      root.style.removeProperty("--ys-focus");
    }
    // At 50 the source palette remains untouched; other values adjust secondary text and borders.
    if (c !== 50) {
      values["--ys-muted"] = `hsl(0 0% ${dark ? 55 + c * 0.3 : 42 - c * 0.2}%)`;
      values["--ys-line"] =
        `rgb(${dark ? "255 255 255" : "0 0 0"} / ${0.06 + c * 0.002})`;
    } else {
      root.style.removeProperty("--ys-muted");
      root.style.removeProperty("--ys-line");
    }
    for (const [key, variable] of [
      ["background", "--ys-canvas"],
      ["foreground", "--ys-text"],
    ]) {
      if (prefs[key] !== "auto") values[variable] = prefs[key];
      else root.style.removeProperty(variable);
    }
    if (prefs.accent !== "auto") {
      const luminance = [1, 3, 5]
        .map((i) => parseInt(prefs.accent.slice(i, i + 2), 16) / 255)
        .map((v) => (v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4))
        .reduce((n, v, i) => n + v * [0.2126, 0.7152, 0.0722][i], 0);
      values["--ys-on-accent"] = luminance > 0.179 ? "#111111" : "#ffffff";
    } else root.style.removeProperty("--ys-on-accent");
    if (palette.accentMode === "gradient" && palette.onAccent === "auto") {
      const luminance = (hex) =>
        [1, 3, 5]
          .map((i) => parseInt(hex.slice(i, i + 2), 16) / 255)
          .map((v) => (v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4))
          .reduce((n, v, i) => n + v * [0.2126, 0.7152, 0.0722][i], 0);
      const valuesAtStops = palette.accentGradient.stops.map(luminance),
        darkScore = Math.min(
          ...valuesAtStops.map((l) => (l + 0.05) / (0.0056 + 0.05)),
        ),
        lightScore = Math.min(...valuesAtStops.map((l) => 1.05 / (l + 0.05)));
      values["--ys-on-accent"] =
        darkScore >= lightScore ? "#111111" : "#ffffff";
    }
    for (const [key, variable] of Object.entries({
      panel: "--ys-panel",
      muted: "--ys-muted",
      border: "--ys-line",
      hover: "--ys-action-hover",
      active: "--ys-action-pressed",
      focus: "--ys-focus",
      onAccent: "--ys-on-accent",
    })) {
      if (palette[key] !== "auto") values[variable] = palette[key];
      else if (!values[variable]) root.style.removeProperty(variable);
    }
    Object.assign(values, {
      "--ys-button-background":
        palette.accentMode === "gradient"
          ? gradient(palette.accentGradient)
          : "var(--ys-accent)",
      "--recipe-accent-image":
        palette.accentMode === "gradient"
          ? gradient(palette.accentGradient)
          : "none",
      "--ys-button-content": "var(--ys-on-accent)",
      "--ys-button-hover":
        palette.hover !== "auto"
          ? palette.hover
          : "color-mix(in srgb,var(--ys-accent) 85%,var(--ys-text))",
      "--ys-button-pressed":
        palette.active !== "auto"
          ? palette.active
          : "color-mix(in srgb,var(--ys-accent) 70%,var(--ys-canvas))",
      "--ys-button-focus": "var(--ys-focus)",
      "--recipe-button-hover":
        palette.hover === "auto"
          ? "var(--ys-button-background)"
          : palette.hover,
      "--recipe-button-pressed":
        palette.active === "auto"
          ? "var(--ys-button-background)"
          : palette.active,
      "--recipe-input-base":
        palette.inputBackground === "auto"
          ? "var(--ys-panel)"
          : palette.inputBackground,
      "--ys-input-background": `color-mix(in srgb,var(--recipe-input-base) ${palette.inputOpacity}%,transparent)`,
      "--ys-input-content":
        palette.inputForeground === "auto"
          ? "var(--ys-text)"
          : palette.inputForeground,
      "--recipe-input-border-base":
        palette.inputBorder === "auto" ? "var(--ys-line)" : palette.inputBorder,
      "--ys-input-border": `color-mix(in srgb,var(--recipe-input-border-base) ${palette.inputBorderOpacity}%,transparent)`,
      "--recipe-nav-base":
        palette.navBackground === "auto"
          ? "var(--ys-panel)"
          : palette.navBackground,
      "--recipe-nav-background": `color-mix(in srgb,var(--recipe-nav-base) ${palette.navOpacity}%,transparent)`,
      "--recipe-nav-selected":
        palette.navSelected === "auto"
          ? "color-mix(in srgb,var(--ys-text) 18%,var(--ys-panel))"
          : palette.navSelected,
      "--recipe-nav-foreground":
        palette.navForeground === "auto"
          ? "var(--ys-muted)"
          : palette.navForeground,
      "--recipe-nav-active-foreground":
        palette.navActiveForeground === "auto"
          ? "var(--ys-text)"
          : palette.navActiveForeground,
      "--recipe-control-base":
        palette.controlBackground === "auto"
          ? "var(--ys-panel)"
          : palette.controlBackground,
      "--recipe-control-background": `color-mix(in srgb,var(--recipe-control-base) ${palette.controlOpacity}%,transparent)`,
      "--recipe-control-hover":
        palette.controlHover === "auto"
          ? "color-mix(in srgb,var(--recipe-control-base) 85%,var(--ys-text))"
          : palette.controlHover,
      "--recipe-control-foreground":
        palette.controlForeground === "auto"
          ? "var(--ys-text)"
          : palette.controlForeground,
      "--recipe-surface-image":
        palette.surfaceBackgroundMode === "gradient"
          ? gradient(palette.surfaceGradient).replace(
              /#[a-f\d]{6}(?![a-f\d])/gi,
              (hex) =>
                `color-mix(in srgb,${hex} var(--recipe-surface-opacity,100%),transparent)`,
            )
          : "none",
    });
    values["--recipe-border-base"] =
      palette.border !== "auto"
        ? palette.border
        : c !== 50
          ? `rgb(${dark ? "255 255 255" : "0 0 0"} / ${0.06 + c * 0.002})`
          : "var(--ds-semantic-color-border-default)";
    values["--ys-line"] =
      `color-mix(in srgb,var(--recipe-border-base) ${palette.borderOpacity}%,transparent)`;
    let sheet = document.getElementById("yeshan-appearance-profile");
    if (!sheet) {
      sheet = document.createElement("style");
      sheet.id = "yeshan-appearance-profile";
      document.head.append(sheet);
    }
    sheet.textContent =
      "html:root[data-portal-theme] > body.ys-theme {--ys-font:" +
      fonts[prefs.font] +
      ";" +
      Object.entries(values)
        .map(([k, v]) => k + ":" + v + ";")
        .join("") +
      "}";
    for (const [k, v] of Object.entries(values)) root.style.setProperty(k, v);
    const b = document.getElementById("themeToggle");
    if (b) {
      if (b.dataset.theme !== effective()) {
        b.dataset.theme = effective();
        b.innerHTML = `<span class="theme-current" aria-hidden="true">${dark ? "☾" : "☀"}</span><span class="theme-target" aria-hidden="true">${dark ? "☀" : "☾"}</span>`;
      }
      b.title = b.ariaLabel = dark ? "切换到亮色主题" : "切换到暗色主题";
    }
    for (const [id, k] of [
      ["themePreference", "theme"],
      ["panelMaterial", "panel"],
      ["cardMaterial", "card"],
    ]) {
      const n = document.getElementById(id);
      if (n) n.value = prefs[k];
    }
    let persisted = true;
    if (save && !rootExport())
      try {
        localStorage.setItem(key, JSON.stringify(prefs));
      } catch {
        persisted = false;
      }
    schedule();
    window.dispatchEvent(new Event("yeshan:appearance"));
    return persisted;
  }
  function set(next) {
    window.YeshanRecipeStore?.beforeChange();
    next = { ...next };
    const densityPresets = structuredClone(
      next.densityPresets || prefs.densityPresets,
    );
    const densityMode = next.densityMode || prefs.densityMode;
    if (next.densityMode && !next.densityPresets) {
      Object.assign(next, densityPresets[densityMode]);
      window.YeshanStyleSystem?.set({ gap: next.gap });
    }
    if (densityPresets[densityMode])
      for (const k of Object.keys(densityPresets[densityMode]))
        if (k in next) densityPresets[densityMode][k] = next[k];
    next.densityPresets = densityPresets;
    const surfaces = structuredClone(prefs.surfaces);
    for (const role of ["panel", "card"])
      for (const type of ["plain", "frosted", "clear"])
        Object.assign(surfaces[role][type], next?.surfaces?.[role]?.[type]);
    const palettes = structuredClone(prefs.palettes);
    for (const mode of ["light", "dark"])
      Object.assign(palettes[mode], next?.palettes?.[mode]);
    if (!next?.palettes) {
      const mode = ["light", "dark"].includes(next?.theme)
        ? next.theme
        : effective();
      for (const k of ["accent", "background", "foreground"])
        if (k in (next || {})) palettes[mode][k] = next[k];
    }
    prefs = normalize({ ...prefs, ...next, surfaces, palettes });
    return apply(window.YeshanRecipeStore?.shouldPersist() !== false);
  }
  function ready() {
    apply();
    document
      .getElementById("themeToggle")
      ?.addEventListener("click", () =>
        set({ theme: effective() === "dark" ? "light" : "dark" }),
      );
    for (const [id, k] of [
      ["themePreference", "theme"],
      ["panelMaterial", "panel"],
      ["cardMaterial", "card"],
    ])
      document
        .getElementById(id)
        ?.addEventListener("change", (e) => set({ [k]: e.target.value }));
    new MutationObserver((records) => {
      if (
        records.some((r) =>
          [...r.addedNodes, ...r.removedNodes].some(
            (n) =>
              n.nodeType === 1 &&
              n.namespaceURI !== "http://www.w3.org/2000/svg",
          ),
        )
      )
        schedule();
    }).observe(document.body, { childList: true, subtree: true });
    addEventListener("yeshan:style", schedule);
  }
  window.YeshanAppearance = {
    get: () => structuredClone(prefs),
    set,
    defaults: structuredClone(defaults),
    normalize,
    effective,
    palette: () => structuredClone(prefs.palettes[effective()]),
    setPalette: (patch, mode = effective()) =>
      set({ palettes: { [mode]: patch } }),
    gradient,
    gradientStops,
    reset: () => set(defaults),
    refresh: schedule,
  };
  apply();
  if (document.readyState === "loading")
    document.addEventListener("DOMContentLoaded", ready);
  else ready();
  media.addEventListener("change", () => {
    if (prefs.theme === "system") apply();
  });
  addEventListener("storage", (e) => {
    if (e.key === key)
      try {
        prefs = normalize(JSON.parse(e.newValue || "{}"));
        apply();
      } catch {}
  });
})();

},"system/style-system.js":function(capsule,published,resolve){/* One persisted, exportable portal profile. Formal token sources remain source.json. */
(() => {
  const key = "yeshan-layout-profile-v1";
  const isolated =
    typeof document !== "undefined" &&
    (document.documentElement.hasAttribute("data-recipe-export") ||
      document.documentElement.hasAttribute("data-portal-embedded"));
  const roles = {
    input: ["输入框", 8],
    button: ["按钮", 10],
    card: ["卡片", 16],
    panel: ["浮空面板", 20],
    editor: ["操作面板", 20],
    highlight: ["导航高亮", 10],
    tabs: ["Tab 胶囊", 28],
  };
  const token = (name, fallback) =>
    (typeof document === "undefined"
      ? fallback
      : parseFloat(
          getComputedStyle(document.documentElement).getPropertyValue(
            "--layout-default-" + name,
          ),
        )) || fallback;
  const defaults = {
    radii: Object.fromEntries(
      Object.entries(roles).map(([key, [, value]]) => [
        key,
        token("radius-" + key, value),
      ]),
    ),
    gap: token("gap", 20),
    small: token("small", 96),
    tabs: "gooey",
    link: {
      radius: 24,
      spread: 4,
      opacity: 100,
      duration: 220,
      color: "auto",
      mode: "inverse",
    },
    units: {},
  };
  function normalize(value = {}) {
    return {
      radii: Object.fromEntries(
        Object.keys(roles).map((k) => [
          k,
          Math.max(
            0,
            Math.min(
              40,
              Number.isFinite(+value.radii?.[k])
                ? +value.radii[k]
                : defaults.radii[k],
            ),
          ),
        ]),
      ),
      gap: Math.max(8, Math.min(32, +value.gap || 20)),
      small: Math.max(80, Math.min(144, +value.small || 96)),
      tabs: ["gooey", "plain"].includes(value.tabs) ? value.tabs : "gooey",
      link: {
        mode: value.link?.mode === "tint" ? "tint" : "inverse",
        ...Object.fromEntries(
          Object.entries({
            radius: [0, 24],
            spread: [0, 8],
            opacity: [0, 100],
            duration: [0, 800],
          }).map(([k, [min, max]]) => [
            k,
            Math.max(
              min,
              Math.min(
                max,
                Number.isFinite(+value.link?.[k])
                  ? +value.link[k]
                  : defaults.link[k],
              ),
            ),
          ]),
        ),
        color: /^#[a-f\d]{6}$/i.test(value.link?.color)
          ? value.link.color
          : "auto",
      },
      units:
        (typeof window === "undefined"
          ? resolve("./unit-properties.js")
          : window.YeshanUnitProperties
        )?.normalize(value.units) || {},
    };
  }
  if (typeof capsule === "object" && capsule.published) {
    capsule.published = { defaults, roles, normalize, css };
    return;
  }
  let profile = normalize();
  try {
    let saved = JSON.parse(isolated ? "{}" : localStorage.getItem(key) || "{}");
    if (window.YeshanEmbed) saved = YeshanEmbed.style.get();
    else if (!isolated) {
      try {
        const draft = JSON.parse(
          sessionStorage.getItem("yeshan-recipe-edit-v2") || "null",
        );
        if (draft?.baseline?.appearance && draft.current?.layout)
          saved = draft.current.layout;
      } catch {}
    }
    profile = normalize(saved);
  } catch {}
  const get = () => structuredClone(profile);
  function css(value = profile) {
    return (
      ":root{" +
      Object.entries(value.radii)
        .map(([k, v]) => "--layout-radius-" + k + ":" + v + "px;")
        .join("") +
      "--ys-layout-gap:" +
      value.gap +
      "px;--ys-card-small-min:" +
      value.small +
      "px;" +
      Object.entries(value.link || defaults.link)
        .filter(([k]) => k !== "mode")
        .map(
          ([k, v]) =>
            "--link-" +
            k +
            ":" +
            (k === "color"
              ? v === "auto"
                ? "var(--ys-text)"
                : v
              : v + (k === "duration" ? "ms" : k === "opacity" ? "%" : "px")) +
            ";",
        )
        .join("") +
      (value.link?.mode === "tint"
        ? "--link-feedback-background:color-mix(in srgb,var(--link-color) var(--link-opacity),transparent);--link-feedback-color:var(--ys-text);"
        : "--link-feedback-background:var(--ds-semantic-color-selection-background);--link-feedback-color:var(--ds-semantic-color-selection-content);") +
      "}" +
      ((typeof window === "undefined"
        ? resolve("./unit-properties.js")
        : window.YeshanUnitProperties
      )?.css(value.units) || "")
    );
  }
  function apply(doc = document) {
    let style = doc.getElementById("yeshan-layout-profile");
    if (!style) {
      style = doc.createElement("style");
      style.id = "yeshan-layout-profile";
      doc.head.append(style);
    }
    style.textContent = css();
    doc.documentElement.dataset.layoutSystem = "true";
    doc.documentElement.dataset.layoutTabs = profile.tabs;
    doc.documentElement.dataset.linkMode = profile.link.mode;
    doc
      .querySelectorAll(".ys-motion-tabs:not([data-local-tabs])")
      .forEach((n) => (n.dataset.tabsAppearance = profile.tabs));
    doc.defaultView?.dispatchEvent(new Event("yeshan:style"));
  }
  function set(next, replace = false) {
    window.YeshanRecipeStore?.beforeChange();
    profile = normalize({
      ...(replace ? defaults : profile),
      ...next,
      radii: { ...(replace ? defaults.radii : profile.radii), ...next.radii },
      link: { ...(replace ? defaults.link : profile.link), ...next.link },
      units:
        next.units === null
          ? {}
          : { ...(replace ? {} : profile.units), ...next.units },
    });
    try {
      if (!isolated && window.YeshanRecipeStore?.shouldPersist() !== false)
        localStorage.setItem(key, JSON.stringify(profile));
    } catch {}
    apply();
  }
  window.YeshanStyleSystem = {
    get,
    set,
    reset: () => set(defaults, true),
    roles,
    defaults,
    normalize,
    css,
  };
  apply();
  addEventListener("storage", (e) => {
    if (e.key === key) {
      try {
        profile = normalize(JSON.parse(e.newValue || "{}"));
        apply();
      } catch {}
    }
  });
})();

},"system/recipe-output.js":function(capsule,published,resolve){/* A frozen recipe snapshot travels with each deliverable. No writes to the site's active recipe. */
(() => {
  const native = typeof capsule === "object" && capsule.published;
  const YeshanAppearance = native
    ? resolve("../portal/appearance.js")
    : window.YeshanAppearance;
  const YeshanStyleSystem = native
    ? resolve("./style-system.js")
    : window.YeshanStyleSystem;
  function css(snapshot, mode) {
    if (!snapshot?.appearance) return "";
    const a = YeshanAppearance.normalize(snapshot.appearance),
      p = a.palettes[mode === "light" ? "light" : "dark"],
      layout = YeshanStyleSystem.normalize(snapshot.layout || {});
    const palette = {
      background: "--ys-canvas",
      panel: "--ys-panel",
      foreground: "--ys-text",
      muted: "--ys-muted",
      accent: "--ys-accent",
      onAccent: "--ys-on-accent",
      border: "--ys-line",
      focus: "--ys-focus",
      /* 主操作的按下与悬停也是角色：写成变量，交付里才不会出现算出来的字面量。 */
      hover: "--ys-accent-hover",
      active: "--ys-accent-active",
    };
    const variables = {};
    for (const [k, v] of Object.entries(palette))
      if (p[k] !== "auto") variables[v] = p[k];
    if (a.contrast !== 50) {
      if (p.muted === "auto")
        variables["--ys-muted"] =
          `hsl(0 0% ${mode === "dark" ? 55 + a.contrast * 0.3 : 42 - a.contrast * 0.2}%)`;
      if (p.border === "auto")
        variables["--ys-line"] =
          `rgb(${mode === "dark" ? "255 255 255" : "0 0 0"} / ${0.06 + a.contrast * 0.002})`;
    }
    if (p.accent !== "auto" && p.onAccent === "auto") {
      const lum = [1, 3, 5]
        .map((i) => parseInt(p.accent.slice(i, i + 2), 16) / 255)
        .map((v) => (v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4))
        .reduce((s, v, i) => s + v * [0.2126, 0.7152, 0.0722][i], 0);
      variables["--ys-on-accent"] = lum > 0.179 ? "#111111" : "#ffffff";
    }
    if (p.accentMode === "gradient" && p.onAccent === "auto") {
      const luminance = (hex) =>
        [1, 3, 5]
          .map((i) => parseInt(hex.slice(i, i + 2), 16) / 255)
          .map((v) => (v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4))
          .reduce((n, v, i) => n + v * [0.2126, 0.7152, 0.0722][i], 0);
      const stops = p.accentGradient.stops.map(luminance);
      const darkScore = Math.min(
          ...stops.map((l) => (l + 0.05) / (0.0056 + 0.05)),
        ),
        lightScore = Math.min(...stops.map((l) => 1.05 / (l + 0.05)));
      variables["--ys-on-accent"] =
        darkScore >= lightScore ? "#111111" : "#ffffff";
    }
    if (p.muted !== "auto") variables["--ys-subtle"] = p.muted;
    const surface = a.surfaces.card[a.card],
      panel = a.surfaces.panel[a.panel],
      gradient = YeshanAppearance.gradient;
    Object.assign(variables, {
      "--ds-semantic-color-selection-background": "var(--ys-text)",
      "--ds-semantic-color-selection-content": "var(--ys-canvas)",
      "--recipe-border": `color-mix(in srgb,var(--ys-line) ${p.borderOpacity}%,transparent)`,
      "--recipe-card-border-width": surface.border + "px",
      "--recipe-panel-border-width": panel.border + "px",
      "--recipe-input-text":
        p.inputForeground === "auto" ? "var(--ys-text)" : p.inputForeground,
      "--recipe-input-border": `color-mix(in srgb,${p.inputBorder === "auto" ? "var(--ys-line)" : p.inputBorder} ${p.inputBorderOpacity}%,transparent)`,
      "--recipe-control-bg":
        p.controlBackground === "auto"
          ? "var(--ys-panel)"
          : p.controlBackground,
      "--recipe-control-hover":
        p.controlHover === "auto"
          ? "var(--ys-raised,var(--ys-panel))"
          : p.controlHover,
      "--recipe-control-text":
        p.controlForeground === "auto" ? "var(--ys-text)" : p.controlForeground,
      "--recipe-nav-bg": `color-mix(in srgb,${p.navBackground === "auto" ? "var(--ys-canvas)" : p.navBackground} ${p.navOpacity}%,transparent)`,
      "--recipe-nav-text":
        p.navForeground === "auto" ? "var(--ys-muted)" : p.navForeground,
      "--recipe-nav-active":
        p.navSelected === "auto" ? "var(--ys-panel)" : p.navSelected,
      "--recipe-nav-active-text":
        p.navActiveForeground === "auto"
          ? "var(--ys-text)"
          : p.navActiveForeground,
      "--ys-font": {
        interface: "Mluvka,system-ui,sans-serif",
        system: "system-ui,sans-serif",
        editorial: '"Songti SC","Noto Serif SC",serif',
      }[a.font],
      "--recipe-background-image": gradient(p),
      "--recipe-surface-image":
        p.surfaceBackgroundMode === "gradient"
          ? gradient(p.surfaceGradient).replace(
              /#[a-f\d]{6}(?![a-f\d])/gi,
              (c) => `color-mix(in srgb,${c} ${surface.opacity}%,transparent)`,
            )
          : "none",
      "--recipe-button-background":
        p.accentMode === "gradient"
          ? gradient(p.accentGradient)
          : "var(--ys-accent)",
      "--ys-button-background": "var(--recipe-button-background)",
      "--recipe-padding": a.padding + "px",
      "--recipe-gap": layout.gap + "px",
      "--recipe-duration": a.duration + "ms",
      "--recipe-font-size": a.textSize + "px",
      "--recipe-line-height": a.lineHeight,
      "--recipe-tracking": a.tracking + "em",
      "--recipe-weight": a.weight,
      "--recipe-card-fill": `color-mix(in srgb,var(--ys-panel) ${surface.opacity}%,transparent)`,
      "--recipe-panel-fill": `color-mix(in srgb,var(--ys-panel) ${panel.opacity}%,transparent)`,
      "--recipe-card-blur":
        a.card === "plain" ? "none" : `blur(${surface.blur}px)`,
      "--recipe-panel-blur":
        a.panel === "plain" ? "none" : `blur(${panel.blur}px)`,
      "--recipe-card-shadow": `0 ${surface.shadow / 3}px ${surface.shadow}px #0002`,
      "--ys-input-background": `color-mix(in srgb,${p.inputBackground === "auto" ? "var(--ys-panel)" : p.inputBackground} ${p.inputOpacity}%,transparent)`,
    });
    const root =
      ":root,:host{" +
      Object.entries(variables)
        .map(([k, v]) => k + ":" + v + ";")
        .join("") +
      "}";
    let result =
      root +
      YeshanStyleSystem.css(layout).replace(":root{", ":root,:host{") +
      `
      body,.delivery-sample-body{font-family:var(--ys-font);font-size:var(--recipe-font-size);font-weight:var(--recipe-weight);letter-spacing:var(--recipe-tracking);background:var(--ys-canvas);background-image:var(--recipe-background-image)}
      .sample-web,.sample-plugin,.sample-reading,.sample-deck,.sample-card,.sample-social{background:transparent;color:var(--ys-text)}
      .delivery-sample-body :is(p,li),body :is(p,li){line-height:var(--recipe-line-height)}
      :is(.sample-web,.sample-plugin,.sample-reading,.sample-card,.sample-social) h1{font-weight:var(--recipe-weight)}
      .web-invites article,.plugin-cards article,.sample-card{border-radius:var(--layout-radius-card);background-color:var(--recipe-card-fill);background-image:var(--recipe-surface-image);backdrop-filter:var(--recipe-card-blur);border-color:var(--recipe-border);box-shadow:var(--recipe-card-shadow)}
      .plugin-columns aside{background:var(--recipe-panel-fill);backdrop-filter:var(--recipe-panel-blur);border-radius:var(--layout-radius-panel)}
      .ds-document input,.ds-document select,.ds-document textarea{background:var(--ys-input-background);color:var(--recipe-input-text);border-color:var(--recipe-input-border);border-radius:var(--layout-radius-input)}
      .ds-document button:not(.sample-primary){background:var(--recipe-control-bg);color:var(--recipe-control-text)}
      .ds-document button:not(.sample-primary):hover{background:var(--recipe-control-hover)}
      .ds-document .deck-nav,.ds-document .chapter-nav{background:var(--recipe-nav-bg);color:var(--recipe-nav-text);border-radius:var(--layout-radius-tabs)}
      .ds-document .chapter-nav a{color:var(--recipe-nav-text)}
      .ds-document [aria-current=page],.ds-document [aria-current=location]{background:var(--recipe-nav-active);color:var(--recipe-nav-active-text)}
      .ds-document .ds-visual,.ds-document .plugin-cards article,.ds-document.sample-card,.ds-document .web-invites button{border-width:var(--recipe-card-border-width);border-color:var(--recipe-border);box-shadow:var(--recipe-card-shadow)}
      .ds-document .plugin-columns aside{border-width:var(--recipe-panel-border-width);border-color:var(--recipe-border)}
      .ds-document .sample-primary{border-radius:var(--layout-radius-button);background:var(--recipe-button-background);color:var(--ys-on-accent);border:1px solid transparent;transition:background var(--recipe-duration),filter var(--recipe-duration)}
      .ds-document .sample-primary:hover{filter:brightness(1.08)}
      .ds-document .sample-primary:focus-visible{outline:2px solid var(--ys-focus,var(--ys-accent));outline-offset:3px}
      .web-hero h2{color:var(--ys-text)}
      .sample-reading,.sample-social,.sample-card{border-color:var(--recipe-border)}
    `;
    if (a.motion === "reduced" || a.duration === 0)
      result += ".ds-art i{animation:none}";
    if (a.buttonStyle === "outline")
      result +=
        ".ds-document .sample-primary{background:transparent;color:var(--ys-accent);border-color:var(--ys-accent)}";
    if (a.buttonStyle === "soft")
      result +=
        ".ds-document .sample-primary{background:color-mix(in srgb,var(--ys-accent) 16%,transparent);color:var(--ys-accent)}";
    if (p.hover !== "auto")
      result +=
        ".ds-document .sample-primary:hover{background:var(--ys-accent-hover);filter:none}";
    if (p.active !== "auto")
      result +=
        ".ds-document .sample-primary:active{background:var(--ys-accent-active);filter:none}";
    return result;
  }
  function effects(scope, appearance) {
    const kind = appearance?.buttonStyle;
    if (!["beam", "metal"].includes(kind)) return { destroy() {} };
    const views = [],
      sheets = [];
    let disposed = false,
      timer,
      attempts = 0;
    function mount() {
      if (disposed) return;
      if (!window.YeshanLibraries) {
        if (attempts++ < 20) timer = setTimeout(mount, 250);
        return;
      }
      for (const button of scope.querySelectorAll(".sample-primary")) {
        button.dataset.sitePrimary = "";
        views.push(
          YeshanLibraries[kind](
            button,
            kind === "metal"
              ? appearance.applications?.site?.metal || {
                  preset: "silver",
                  strength: 1,
                }
              : { size: "sm" },
          ),
        );
        if (scope !== document) {
          const ids =
            kind === "metal"
              ? [document.getElementById("metal-fx-styles")]
              : [...document.head.querySelectorAll("style")].filter((n) =>
                  n.textContent.includes(button.dataset.beam),
                );
          for (const source of ids)
            if (source) {
              const copy = source.cloneNode(true);
              copy.removeAttribute("id");
              scope.prepend(copy);
              sheets.push(copy);
            }
        }
      }
    }
    mount();
    return {
      destroy() {
        disposed = true;
        clearTimeout(timer);
        views.forEach((v) => v.destroy());
        sheets.forEach((s) => s.remove());
      },
    };
  }
  if (native) capsule.published = { css };
  else window.YeshanRecipeOutput = { css, effects };
})();

}},cache={};function load(id){if(cache[id])return cache[id].published;const capsule=cache[id]={published:{}};modules[id](capsule,capsule.published,p=>{const parts=id.split('/');parts.pop();for(const v of p.split('/'))if(v==='..')parts.pop();else if(v!=='.')parts.push(v);return load(parts.join('/'));});return capsule.published;}window.YeshanRecipeOutput=load('system/recipe-output.js');})();
/** Consumer metadata only. Shared motion implementation and rendered content stay authoritative. */
(()=>{
 const mounts=new WeakMap();
 const mount=node=>{let id=mounts.get(node);if(!id){id=crypto.randomUUID();mounts.set(node,id);}return id;};
 const stamp=()=>{
  for(const node of document.querySelectorAll('[data-motion-surface="website"][data-motion-entity],[data-motion-surface="cms-preview"][data-motion-entity]')){
   const physical=mount(node);node.dataset.motionMount=physical;node.dataset.motionId=node.dataset.motionEntity+'-'+physical;
  }
  const nav=document.querySelector('.site-nav[data-motion-surface="website"],.site-nav[data-motion-surface="cms-preview"]');
  if(!nav)return;
  const geometry=nav.dataset.motionSurface==='cms-preview'?'preview-navigation-geometry':'website-navigation-geometry';
  for(const rect of nav.querySelectorAll('.ys-motion-tabs-fluid rect')){
   const physical=mount(rect);rect.dataset.motionMount=physical;
   rect.dataset.motionId=geometry+'-'+physical;
   rect.dataset.motionEntity=geometry;
   rect.dataset.motionSurface=nav.dataset.motionSurface;rect.dataset.motionAction='navigation-geometry';
   rect.dataset.motionOwner=nav.dataset.motionEntity;
   rect.dataset.motionBusinessKey=nav.dataset.motionBusinessKey;
  }
 };
 let observer;
 const attach=()=>{stamp();if(observer)return;observer=new MutationObserver(stamp);observer.observe(document.documentElement,{childList:true,subtree:true});};
 window.YouyangMotionInventory={stamp};
 attach();
 addEventListener('pagehide',()=>{observer?.disconnect();observer=null;});
 addEventListener('pageshow',event=>{if(event.persisted)attach();});
})();

/* Native shared-indicator tabs. Motion reference: https://beui.dev/components/motion/tabs
 * An explicit duration uses real Web Animations on the visible SVG rectangles.
 * Unspecified duration retains the analytic 170 / 24 / 1.2 spring API.
 */
(() => {
  "use strict";
  const mounted = new WeakMap();
  let serial = 0;
  const attrs = [
    "role",
    "tabindex",
    "aria-selected",
    "aria-current",
    "aria-pressed",
  ];
  const setAttr = (node, name, value) => {
    if (value === null) {
      if (node.hasAttribute(name)) node.removeAttribute(name);
    } else if (node.getAttribute(name) !== String(value))
      node.setAttribute(name, value);
  };

  // Analytic spring integration preserves current position AND velocity on reversal.
  function step(position, velocity, target, seconds, spring) {
    const omega = Math.sqrt(spring.stiffness / spring.mass);
    const damping = spring.damping / (2 * spring.mass);
    const offset = position - target;
    if (Math.abs(damping - omega) < 0.0001) {
      const b = velocity + damping * offset;
      const decay = Math.exp(-damping * seconds);
      return [
        target + (offset + b * seconds) * decay,
        (velocity - damping * b * seconds) * decay,
      ];
    }
    if (damping < omega) {
      const frequency = Math.sqrt(omega * omega - damping * damping);
      const angle = frequency * seconds;
      const decay = Math.exp(-damping * seconds);
      const b = (velocity + damping * offset) / frequency;
      const displaced = offset * Math.cos(angle) + b * Math.sin(angle);
      return [
        target + decay * displaced,
        decay *
          (-damping * displaced -
            offset * frequency * Math.sin(angle) +
            b * frequency * Math.cos(angle)),
      ];
    }
    const root = Math.sqrt(damping * damping - omega * omega);
    const r1 = -damping + root,
      r2 = -damping - root;
    const a = (velocity - r2 * offset) / (r1 - r2),
      b = offset - a;
    return [
      target + a * Math.exp(r1 * seconds) + b * Math.exp(r2 * seconds),
      a * r1 * Math.exp(r1 * seconds) + b * r2 * Math.exp(r2 * seconds),
    ];
  }

  function mount(root, options = {}) {
    if (!(root instanceof HTMLElement))
      throw new TypeError("Motion tabs need a root element.");
    if (mounted.has(root)) return mounted.get(root);
    const items = [
      ...root.querySelectorAll(
        options.selector ||
          ":scope > a, :scope > button, :scope > [data-tab-value]",
      ),
    ];
    if (!items.length)
      throw new Error("Motion tabs need at least one direct trigger.");
    const filtering = options.mode === "filter";
    const navigation =
      options.mode === "navigation" ||
      (!filtering &&
        options.mode !== "tabs" &&
        items.every((x) => x.matches("a[href]")));
    const originalRootRole = root.getAttribute("role"),
      originalOrientation = root.getAttribute("aria-orientation");
    const originals = items.map((item) =>
      Object.fromEntries(attrs.map((key) => [key, item.getAttribute(key)])),
    );
    const values = items.map(
      (item, i) =>
        item.dataset.tabValue ||
        item.dataset.domain ||
        item.getAttribute("value") ||
        String(i),
    );
    if (new Set(values).size !== values.length)
      throw new Error("Motion tab values must be unique.");
    const springValues = (settings) => {
      const result = { stiffness: 170, damping: 24, mass: 1.2, ...settings };
      if (
        Object.values(result).some(
          (value) => !Number.isFinite(value) || value <= 0,
        )
      )
        throw new TypeError("Spring values must be positive finite numbers.");
      return result;
    };
    let spring = springValues(options.spring);
    let paused = false,
      speed = options.speed ?? 1;
    if (!Number.isFinite(speed) || speed <= 0 || speed > 8)
      throw new TypeError("Motion speed must be in (0, 8].");
    if (
      options.duration !== undefined &&
      (!Number.isFinite(options.duration) || options.duration < 0)
    )
      throw new TypeError(
        "Motion duration must be a finite nonnegative number.",
      );
    let tweens = [];
    let dead = false,
      raf = 0,
      previousTime = 0,
      initialized = false;
    let current =
      options.value ??
      values[
        items.findIndex((x) =>
          x.matches(
            '[aria-selected="true"], [aria-current], [aria-pressed="true"]',
          ),
        )
      ] ??
      values[0];
    let reduced = options.reducedMotion;
    const media = matchMedia("(prefers-reduced-motion: reduce)");
    const dimensions = ["x", "y", "width", "height"];
    const state = { x: 0, y: 0, width: 0, height: 0 };
    const velocity = { x: 0, y: 0, width: 0, height: 0 };
    let target = { ...state };
    const svgNS = "http://www.w3.org/2000/svg",
      shape = document.createElementNS(svgNS, "svg");
    const filterId = "ys-tabs-goo-" + ++serial;
    shape.setAttribute("width", "0");
    shape.setAttribute("height", "0");
    shape.classList.add("ys-motion-tabs-fluid");
    shape.setAttribute("aria-hidden", "true");
    shape.setAttribute("focusable", "false");
    shape.innerHTML = `<defs><filter id="${filterId}" x="-20%" y="-70%" width="140%" height="240%" color-interpolation-filters="sRGB"><feGaussianBlur in="SourceGraphic" stdDeviation="4" result="blur"/><feColorMatrix in="blur" type="matrix" values="1 0 0 0 0 0 1 0 0 0 0 0 1 0 0 0 0 0 18 -7"/></filter></defs><g filter="url(#${filterId})"><rect/><rect/></g>`;
    const blobs = [...shape.querySelectorAll("rect")],
      tail = { ...state };
    root.prepend(shape);
    if (options.appearance) root.dataset.localTabs = "true";
    root.dataset.tabsAppearance =
      options.appearance || window.YeshanStyleSystem?.get().tabs || "gooey";
    root.classList.add("ys-motion-tabs");
    if (options.stretch) root.classList.add("ys-motion-tabs-stretch");
    if (options.variant === "list") root.classList.add("ys-motion-tabs-list");
    root.dataset.motionTabsMode = navigation
      ? "navigation"
      : filtering
        ? "filter"
        : "tabs";
    function orientation() {
      root.dataset.motionAxis = options.orientation || "horizontal";
      if (!navigation && !filtering)
        setAttr(root, "aria-orientation", root.dataset.motionAxis);
    }
    orientation();
    if (!navigation) setAttr(root, "role", filtering ? "group" : "tablist");
    items.forEach((item) => item.classList.add("ys-motion-tab"));

    function blocked() {
      return (
        reduced === true ||
        parseFloat(
          getComputedStyle(root).getPropertyValue("--recipe-duration"),
        ) === 0 ||
        document.documentElement.dataset.recipeMotion === "none" ||
        media.matches ||
        document.body.dataset.reduced === "true" ||
        document.body.dataset.reduceMotion === "true" ||
        document.hidden
      );
    }
    function box(item) {
      const host = root.getBoundingClientRect(),
        rect = item.getBoundingClientRect();
      const style = getComputedStyle(root);
      // Coordinates are local to the control, including inside a scaled or scrolled host.
      const scaleX = host.width / parseFloat(style.width) || 1;
      const scaleY = host.height / parseFloat(style.height) || 1;
      return {
        x: (rect.left - host.left) / scaleX - root.clientLeft + root.scrollLeft,
        y: (rect.top - host.top) / scaleY - root.clientTop + root.scrollTop,
        width: rect.width / scaleX,
        height: rect.height / scaleY,
      };
    }
    function paint(preserveTail = false) {
      const immediate = blocked() || root.dataset.tabsAppearance === "plain";
      const radius = getComputedStyle(root).getPropertyValue(
        options.orientation === "vertical"
          ? "--layout-radius-highlight"
          : "--layout-radius-tabs",
      );
      shape.querySelector("g").style.filter =
        radius.trim() && parseFloat(radius) === 0 ? "none" : "";
      dimensions.forEach(
        (k) =>
          (tail[k] = preserveTail
            ? tail[k]
            : immediate
              ? state[k]
              : tail[k] + (state[k] - tail[k]) * 0.32),
      );
      [state, tail].forEach((b, i) => {
        for (const key of dimensions)
          blobs[i].setAttribute(
            key,
            Math.max(
              key === "width" || key === "height" ? 0 : -Infinity,
              b[key],
            ),
          );
        blobs[i].setAttribute(
          "rx",
          Math.min(
            b.height / 2,
            getComputedStyle(root)
              .getPropertyValue(
                options.orientation === "vertical"
                  ? "--layout-radius-highlight"
                  : "--layout-radius-tabs",
              )
              .trim()
              ? parseFloat(
                  getComputedStyle(root).getPropertyValue(
                    options.orientation === "vertical"
                      ? "--layout-radius-highlight"
                      : "--layout-radius-tabs",
                  ),
                )
              : options.orientation === "vertical"
                ? 8
                : 999,
          ),
        );
      });
      shape.style.width =
        Math.max(
          root.clientWidth,
          ...items.map((item) => {
            const b = box(item);
            return b.x + b.width + 4;
          }),
        ) + "px";
      shape.style.height = root.clientHeight + "px";
    }
    // SVG 2 geometry properties are animatable CSS lengths, on these actual rects:
    // https://www.w3.org/TR/SVG2/geometry.html (x/y/width/height).
    // Sample the browser's current presentation before cancelling an interrupted
    // tween. No proxy element, fake Animation, or synthetic progress is exposed.
    function sampleTween() {
      if (!tweens.length) return;
      [state, tail].forEach((position, index) => {
        const css = getComputedStyle(blobs[index]);
        dimensions.forEach((key) => {
          const value = parseFloat(css.getPropertyValue(key));
          if (Number.isFinite(value)) position[key] = value;
        });
      });
    }
    function cancelTween() {
      const old = tweens;
      tweens = [];
      old.forEach((animation) => animation.cancel());
    }
    function startTween() {
      if (blobs.some((blob) => typeof blob.animate !== "function"))
        throw new Error(
          "Duration-based motion tabs require Web Animations on SVG elements.",
        );
      const frame = (position) =>
        Object.fromEntries(
          dimensions.map((key) => [key, position[key] + "px"]),
        );
      const end = frame(target);
      // Underlying attributes keep the sampled start until the real animations
      // finish. Both silhouettes share the declared duration; the trailing one
      // has a later easing response so the existing gooey appearance remains.
      paint(true);
      const group = [state, tail].map((position, index) => {
        const animation = blobs[index].animate([frame(position), end], {
          duration: options.duration,
          easing:
            index === 1 && root.dataset.tabsAppearance !== "plain"
              ? "cubic-bezier(0.32, 0, 0.44, 1)"
              : "cubic-bezier(0.22, 0.61, 0.36, 1)",
          fill: "both",
        });
        animation.updatePlaybackRate(speed);
        if (paused) animation.pause();
        return animation;
      });
      tweens = group;
      Promise.all(group.map((animation) => animation.finished)).then(
        () => {
          if (!dead && tweens === group) settle();
        },
        () => {
          /* cancel() rejects finished; cancellation is an expected lifecycle action. */
        },
      );
    }
    function settle() {
      cancelAnimationFrame(raf);
      raf = 0;
      previousTime = 0;
      dimensions.forEach((key) => {
        state[key] = target[key];
        tail[key] = target[key];
        velocity[key] = 0;
      });
      paint();
      cancelTween();
    }
    function tick(time) {
      if (dead || paused) {
        raf = 0;
        return;
      }
      if (blocked()) {
        settle();
        return;
      }
      const dt = previousTime
        ? Math.min((time - previousTime) / 1000, 0.064)
        : 1 / 60;
      previousTime = time;
      let moving = false;
      dimensions.forEach((key) => {
        [state[key], velocity[key]] = step(
          state[key],
          velocity[key],
          target[key],
          dt *
            speed *
            Math.min(
              4,
              380 /
                (parseFloat(
                  getComputedStyle(root).getPropertyValue("--recipe-duration"),
                ) || 380),
            ),
          spring,
        );
        moving ||=
          Math.abs(state[key] - target[key]) > 0.015 ||
          Math.abs(velocity[key]) > 0.025;
      });
      paint();
      if (moving) raf = requestAnimationFrame(tick);
      else settle();
    }
    function measure(animate = true) {
      if (dead || !root.isConnected) return;
      const active = items[values.indexOf(current)];
      if (!active || !active.getClientRects().length) return;
      const next = box(active);
      if (
        tweens.length &&
        animate &&
        !blocked() &&
        dimensions.every((key) => next[key] === target[key])
      )
        return;
      sampleTween();
      // Commit the visible geometry before removing the existing effect.
      if (tweens.length) paint(true);
      cancelTween();
      target = next;
      if (!initialized || !animate || blocked() || options.duration === 0)
        settle();
      else if (options.duration !== undefined) {
        if (
          dimensions.every(
            (key) =>
              Math.abs(state[key] - target[key]) < 0.001 &&
              Math.abs(tail[key] - target[key]) < 0.001,
          )
        )
          settle();
        else startTween();
      } else if (!raf && !paused) {
        previousTime = performance.now();
        raf = requestAnimationFrame(tick);
      }
      initialized = true;
    }
    function refresh() {
      if (dead) return;
      const active = items[values.indexOf(current)];
      if (active && root.clientWidth) reveal(active);
      measure(initialized);
      edges();
    }
    function edges() {
      const vertical = options.orientation === "vertical";
      const offset = vertical ? root.scrollTop : root.scrollLeft;
      const size = vertical ? root.clientHeight : root.clientWidth;
      const total = vertical ? root.scrollHeight : root.scrollWidth;
      root.dataset.overflowStart = String(offset > 2);
      root.dataset.overflowEnd = String(offset + size < total - 3);
    }
    function reveal(item) {
      edges();
      const vertical = options.orientation === "vertical";
      if (
        vertical
          ? root.scrollHeight <= root.clientHeight
          : root.scrollWidth <= root.clientWidth
      )
        return;
      const host = root.getBoundingClientRect(),
        rect = item.getBoundingClientRect();
      const style = getComputedStyle(root);
      const scale = vertical
        ? host.height / parseFloat(style.height) || 1
        : host.width / parseFloat(style.width) || 1;
      const start = vertical ? "top" : "left",
        end = vertical ? "bottom" : "right";
      const inset = vertical ? root.clientTop : root.clientLeft;
      const size = vertical ? root.clientHeight : root.clientWidth;
      const lo = host[start] + (inset + 4) * scale,
        hi = host[start] + (inset + size - 4) * scale;
      const offset = vertical ? root.scrollTop : root.scrollLeft;
      const delta =
        rect[start] < lo
          ? rect[start] - lo
          : rect[end] > hi
            ? rect[end] - hi
            : 0;
      if (delta)
        root.scrollTo({
          [start]: offset + delta / scale,
          behavior: blocked() ? "instant" : "smooth",
        });
    }
    function setValue(value, settings = {}) {
      const index = values.indexOf(String(value));
      if (
        dead ||
        index < 0 ||
        items[index].matches(':disabled,[aria-disabled="true"]')
      )
        return false;
      const changed = current !== values[index];
      current = values[index];
      items.forEach((item, i) => {
        const selected = i === index;
        setAttr(item, "tabindex", selected ? "0" : "-1");
        if (navigation)
          setAttr(
            item,
            "aria-current",
            selected ? options.current || "page" : null,
          );
        else if (filtering) setAttr(item, "aria-pressed", String(selected));
        else {
          setAttr(item, "role", "tab");
          setAttr(item, "aria-selected", String(selected));
        }
      });
      root.dataset.motionTabsValue = current;
      measure(settings.animate !== false);
      if (settings.focus) items[index].focus({ preventScroll: true });
      if (root.clientWidth) reveal(items[index]);
      if (changed && settings.notify)
        options.onValueChange?.(current, {
          trigger: items[index],
          source: settings.source || "api",
        });
      return true;
    }
    function click(event) {
      const item = items.find(
        (x) => x === event.target || x.contains(event.target),
      );
      if (
        !item ||
        event.defaultPrevented ||
        event.button > 0 ||
        event.metaKey ||
        event.ctrlKey ||
        event.shiftKey ||
        event.altKey
      )
        return;
      if (item.matches(':disabled,[aria-disabled="true"]')) {
        event.preventDefault();
        return;
      }
      setValue(values[items.indexOf(item)], {
        notify: true,
        source: "pointer",
      });
      // Anchor navigation remains native, preserving context menu / modified clicks.
    }
    function keydown(event) {
      if (event.defaultPrevented) return;
      const from = items.indexOf(document.activeElement);
      if (from < 0) return;
      const enabled = items
        .map((item, i) =>
          item.matches(':disabled,[aria-disabled="true"]') ? -1 : i,
        )
        .filter((i) => i >= 0);
      if (!enabled.length) return;
      let next;
      const rtl = getComputedStyle(root).direction === "rtl";
      if (event.key === "Home") next = enabled[0];
      else if (event.key === "End") next = enabled.at(-1);
      else if (
        event.key === "ArrowRight" ||
        event.key === "ArrowLeft" ||
        (options.orientation === "vertical" &&
          ["ArrowDown", "ArrowUp"].includes(event.key))
      ) {
        const direction =
          (["ArrowRight", "ArrowDown"].includes(event.key) ? 1 : -1) *
          (rtl ? -1 : 1);
        next =
          enabled[
            (enabled.indexOf(from) + direction + enabled.length) %
              enabled.length
          ];
      } else if (navigation && event.key === " ") {
        event.preventDefault();
        items[from].click();
        return;
      } else return;
      event.preventDefault();
      if (options.activation === "manual") {
        items.forEach((item, i) =>
          setAttr(item, "tabindex", i === next ? "0" : "-1"),
        );
        items[next].focus({ preventScroll: true });
        reveal(items[next]);
      } else {
        setValue(values[next], {
          focus: true,
          notify: true,
          source: "keyboard",
        });
        items[next].click();
      }
    }
    function styleChange() {
      if (!options.appearance)
        root.dataset.tabsAppearance =
          window.YeshanStyleSystem?.get().tabs ||
          root.ownerDocument.documentElement.dataset.layoutTabs ||
          "gooey";
      paint();
    }
    window.addEventListener("yeshan:style", styleChange);
    function motionChange() {
      if (blocked()) settle();
    }
    root.addEventListener("scroll", edges, { passive: true });
    root.addEventListener("click", click);
    root.addEventListener("keydown", keydown);
    media.addEventListener("change", motionChange);
    window.addEventListener("yeshan:motion", motionChange);
    document.addEventListener("visibilitychange", motionChange);
    const motionState = new MutationObserver(motionChange);
    motionState.observe(document.body, {
      attributes: true,
      attributeFilter: ["data-reduced", "data-reduce-motion"],
    });
    const resize = new ResizeObserver(refresh);
    resize.observe(root);
    items.forEach((item) => resize.observe(item));
    const selection = new MutationObserver(() => {
      const active = items.find((x) =>
        x.matches(
          '[aria-selected="true"], [aria-current], [aria-pressed="true"]',
        ),
      );
      if (active) setValue(values[items.indexOf(active)]);
    });
    if (options.observeSelection !== false)
      selection.observe(root, {
        subtree: true,
        attributes: true,
        attributeFilter: ["aria-current", "aria-selected", "aria-pressed"],
      });
    const api = {
      get value() {
        return current;
      },
      get element() {
        return root;
      },
      setValue,
      refresh,
      pause() {
        if (dead) return;
        paused = true;
        tweens.forEach((animation) => animation.pause());
        sampleTween();
        cancelAnimationFrame(raf);
        raf = 0;
        previousTime = 0;
      },
      resume() {
        if (dead || !paused) return;
        paused = false;
        if (tweens.length && !blocked()) {
          tweens.forEach((animation) => animation.play());
          return;
        }
        previousTime = performance.now();
        if (!blocked() && options.duration === undefined)
          raf = requestAnimationFrame(tick);
        else settle();
      },
      setSpeed(value) {
        if (!Number.isFinite(value) || value <= 0 || value > 8)
          throw new TypeError("Motion speed must be in (0, 8].");
        speed = value;
        tweens.forEach((animation) => animation.updatePlaybackRate(speed));
      },
      snapshot() {
        sampleTween();
        return {
          paused,
          speed,
          active:
            Boolean(raf) ||
            tweens.some((animation) => animation.playState === "running"),
          position: { ...state },
          target: { ...target },
        };
      },
      update(settings = {}) {
        if (settings.orientation) {
          options.orientation = settings.orientation;
          orientation();
          refresh();
        }
        if ("reducedMotion" in settings) reduced = settings.reducedMotion;
        if (settings.appearance)
          root.dataset.tabsAppearance = settings.appearance;
        if (settings.spring)
          spring = springValues({ ...spring, ...settings.spring });
        if ("value" in settings) setValue(settings.value);
        if (blocked()) settle();
      },
      destroy() {
        if (dead) return;
        dead = true;
        cancelAnimationFrame(raf);
        raf = 0;
        cancelTween();
        resize.disconnect();
        selection.disconnect();
        motionState.disconnect();
        root.removeEventListener("scroll", edges);
        root.removeEventListener("click", click);
        root.removeEventListener("keydown", keydown);
        media.removeEventListener("change", motionChange);
        window.removeEventListener("yeshan:motion", motionChange);
        document.removeEventListener("visibilitychange", motionChange);
        window.removeEventListener("yeshan:style", styleChange);
        shape.remove();
        delete root.dataset.tabsAppearance;
        root.classList.remove("ys-motion-tabs", "ys-motion-tabs-stretch");
        delete root.dataset.motionTabsValue;
        delete root.dataset.motionTabsMode;
        delete root.dataset.motionAxis;
        root.classList.remove("ys-motion-tabs-list");
        setAttr(root, "aria-orientation", originalOrientation);
        setAttr(root, "role", originalRootRole);
        items.forEach((item, i) => {
          item.classList.remove("ys-motion-tab");
          attrs.forEach((key) => setAttr(item, key, originals[i][key]));
        });
        mounted.delete(root);
      },
    };
    mounted.set(root, api);
    setValue(current, { animate: false });
    refresh();
    document.fonts?.ready.then(() => {
      if (!dead) refresh();
    });
    return api;
  }
  const api = {
    mount,
    isMounted: (root) => mounted.has(root),
    version: "1.3.0",
  };
  if (typeof module === "object" && module.exports) module.exports = api;
  else window.YeshanMotionTabs = api;
})();

/* Details stay beside their source, without a modal page mask. */
(() => {
  let current;
  const transitions = new WeakMap();
  const controllers = new WeakMap();
  const durationOf = (node) => {
    const local = parseFloat(
      getComputedStyle(node).getPropertyValue("--recipe-duration"),
    );
    if (local === 0) return 0;
    return (
      window.YeshanMotionPolicy?.durations.layout ??
      (Number.isFinite(local) ? local : 460)
    );
  };
  function reveal(detail, behavior = "smooth") {
    const scroller = detail.closest(".wb-detail-body");
    if (!scroller) return;
    const r = detail.getBoundingClientRect(),
      s = scroller.getBoundingClientRect();
    const overflow = r.bottom - s.bottom + 12;
    if (overflow > 0)
      scroller.scrollBy({
        top: Math.min(overflow, Math.max(0, r.top - s.top - 8)),
        behavior,
      });
  }
  document.addEventListener("pointerover", (event) => {
    if (!matchMedia("(hover:hover)").matches) return;
    const summary = event.target.closest("[data-hover-disclosures] summary"),
      detail = summary?.parentElement;
    if (!detail || detail.open || summary.contains(event.relatedTarget)) return;
    clearTimeout(detail._hoverTimer);
    detail._hoverTimer = setTimeout(() => {
      if (summary.matches(":hover") && !detail.open) summary.click();
    }, 180);
  });
  // Native summary keeps keyboard semantics; height and content now move together.
  document.addEventListener("click", (event) => {
    const summary = event.target.closest("summary"),
      detail = summary?.parentElement;
    if (
      !detail?.matches("details") ||
      !detail.closest(".wb-projects,.wb-detail-popover,[data-disclosure-group]")
    )
      return;
    event.preventDefault();
    const previous = transitions.get(detail),
      opening = previous ? !previous.opening : !detail.open;
    const from = detail.getBoundingClientRect().height;
    previous?.animation?.cancel();
    detail.style.height = "";
    detail.open = true;
    const to = opening
      ? detail.getBoundingClientRect().height
      : summary.getBoundingClientRect().height +
        parseFloat(getComputedStyle(detail).paddingTop || 0) +
        parseFloat(getComputedStyle(detail).paddingBottom || 0) +
        2;
    const controller = controllers.get(
      detail.closest("[data-disclosure-group]"),
    );
    const duration =
      matchMedia("(prefers-reduced-motion: reduce)").matches ||
      controller?.reduced?.()
        ? 0
        : (controller?.duration ?? durationOf(detail));
    detail.style.overflow = "hidden";
    const animation = controller?.animate
      ? controller.animate(
          detail,
          { height: to + "px" },
          { from: { height: from + "px" }, duration, layout: true },
        )
      : detail.animate([{ height: from + "px" }, { height: to + "px" }], {
          duration,
          easing: "cubic-bezier(.22,1,.36,1)",
        });
    const transition = { animation, opening };
    transitions.set(detail, transition);
    animation.finished
      .then(() => {
        if (transitions.get(detail) !== transition) return;
        detail.open = opening;
        detail.style.overflow = "";
        detail.style.height = "";
        transitions.delete(detail);
        if (opening) reveal(detail, duration ? "smooth" : "instant");
      })
      .catch(() => {});
  });
  function open(title, content, trigger = document.activeElement) {
    current?.close();
    const panel = document.createElement("div"),
      head = document.createElement("header"),
      h = document.createElement("h2"),
      close = document.createElement("button"),
      body = document.createElement("div");
    panel.className = "wb-drawer wb-detail-popover";
    panel.setAttribute("popover", "auto");
    panel.setAttribute("role", "dialog");
    panel.ariaLabel = title;
    h.textContent = title;
    close.type = "button";
    close.className = "p-button";
    close.textContent = "✕";
    close.ariaLabel = "关闭详情";
    head.append(h, close);
    body.className = "wb-detail-body";
    body.append(content);
    panel.append(head, body);
    document.body.append(panel);
    const anchor = trigger?.closest(".wb-project,.wb-task,.ws-day") || trigger;
    let removed = false;
    function position() {
      if (removed || !panel.matches(":popover-open")) return;
      const r = anchor?.getBoundingClientRect() || {
          left: 16,
          right: 16,
          top: 80,
          bottom: 80,
        },
        w = Math.min(410, innerWidth - 24);
      panel.style.width = w + "px";
      panel.style.maxHeight = Math.min(560, innerHeight - 24) + "px";
      let left, top;
      if (innerWidth - r.right >= w + 24) {
        left = r.right + 12;
        top = r.top;
        panel.dataset.side = "right";
      } else if (r.left >= w + 24) {
        left = r.left - w - 12;
        top = r.top;
        panel.dataset.side = "left";
      } else {
        left = Math.max(12, Math.min(innerWidth - w - 12, r.left));
        top = r.bottom + 10;
        panel.dataset.side = "below";
      }
      const height = panel.offsetHeight;
      if (top + height > innerHeight - 12)
        top = Math.max(12, Math.min(r.top, innerHeight - height - 12));
      panel.style.left =
        Math.max(12, Math.min(innerWidth - w - 12, left)) + "px";
      panel.style.top = Math.max(12, top) + "px";
    }
    const finish = () => {
      if (removed) return;
      removed = true;
      observer.disconnect();
      removeEventListener("resize", position);
      removeEventListener("scroll", scroll, true);
      panel.remove();
      if (current === api) current = null;
      if (trigger?.isConnected) trigger.focus({ preventScroll: true });
    };
    const api = {
      close() {
        if (panel.matches(":popover-open")) panel.hidePopover();
        finish();
      },
      element: panel,
    };
    const scroll = (e) => {
      if (!panel.contains(e.target)) position();
    };
    const observer = new ResizeObserver(position);
    observer.observe(body);
    panel.addEventListener("toggle", (e) => {
      if (e.newState === "closed") finish();
    });
    close.onclick = api.close;
    current = api;
    panel.showPopover();
    position();
    const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
    panel.animate(
      [
        {
          opacity: 0,
          translate: panel.dataset.side === "left" ? "6px 0" : "-6px 0",
        },
        { opacity: 1, translate: "0 0" },
      ],
      {
        duration: reduced ? 0 : durationOf(panel),
        easing: "cubic-bezier(.2,.8,.2,1)",
      },
    );
    close.focus({ preventScroll: true });
    addEventListener("resize", position);
    addEventListener("scroll", scroll, true);
    return api;
  }
  window.YeshanDisclosure = {
    open,
    close: () => current?.close(),
    mount(host, { hover = false, controller } = {}) {
      host.dataset.disclosureGroup = "";
      if (controller) controllers.set(host, controller);
      if (hover) host.dataset.hoverDisclosures = "";
      return {
        destroy() {
          for (const detail of host.querySelectorAll("details")) {
            clearTimeout(detail._hoverTimer);
            transitions.get(detail)?.animation?.cancel();
            transitions.delete(detail);
            detail.style.overflow = "";
            detail.style.height = "";
          }
          controllers.delete(host);
          delete host.dataset.disclosureGroup;
          delete host.dataset.hoverDisclosures;
        },
      };
    },
  };
  addEventListener("hashchange", () => current?.close());
})();

(()=>{const recipe={"id":"36a058a5-26cb-4229-8843-593112893db7","name":"裂口陶器 · 图像配方","savedAt":"2026-09-10T17:57:58.880Z","appearance":{"theme":"dark","panel":"clear","card":"clear","accent":"#9C6752","background":"#262725","foreground":"#F6F7F2","contrast":67,"font":"interface","textSize":16,"lineHeight":1.75,"tracking":0.025,"weight":380,"padding":23,"duration":460,"densityMode":"comfortable","densityPresets":{"compact":{"padding":16,"rowHeight":36,"cardRatio":1.8,"lineHeight":1.5,"tracking":0,"textSize":14,"gap":8},"comfortable":{"padding":23,"rowHeight":56,"cardRatio":1.1,"lineHeight":1.75,"tracking":0.025,"textSize":16,"gap":21},"editorial":{"padding":28,"rowHeight":52,"cardRatio":1.1,"lineHeight":1.9,"tracking":0.015,"textSize":18,"gap":28}},"rowHeight":56,"cardRatio":1.1,"previewBackdrop":"page","buttonStyle":"soft","applications":{"version":1,"site":{"metal":{"preset":"chromatic","strength":1},"gooey":{"blur":4}},"workbench":{},"reference":{}},"palettes":{"dark":{"accent":"#9C6752","background":"#262725","foreground":"#F6F7F2","panel":"#1C1D1A","muted":"#C8C8C6","border":"#686562","hover":"#91604C","active":"#895B48","focus":"#9C6752","onAccent":"#FFFFFF","inputBackground":"#363734","inputForeground":"#F6F7F2","inputBorder":"#73706D","inputOpacity":36,"borderOpacity":100,"inputBorderOpacity":100,"navBackground":"#1C1D1A","navSelected":"#3B3C38","navForeground":"#C8C8C6","navActiveForeground":"#F6F7F2","navOpacity":91,"controlBackground":"#1C1D1A","controlHover":"#323330","controlForeground":"#F6F7F2","controlOpacity":78,"surfaceBackgroundMode":"solid","surfaceGradient":{"backgroundMode":"linear","angle":130,"blend":70,"centerX":49,"centerY":12,"stops":["#242b27","#333b30","#25363d"],"weights":null,"positions":[0,46,100],"anchors":[{"x":10,"y":75},{"x":78,"y":70},{"x":50,"y":50}]},"backgroundMode":"radial","angle":102,"positions":[81,34,8,73,72,0],"weights":[48,41.02322949318091,4.152948566269794,0.7784883094588646,1.6054092678812317,4.439924363209196],"centerX":100,"centerY":100,"blend":100,"anchors":[{"x":35.092592592592595,"y":6.507105459985041},{"x":52.5,"y":63.79955123410621},{"x":53.148148148148145,"y":56.99326851159312},{"x":57.68518518518518,"y":51.757666417352276},{"x":46.111111111111114,"y":41.361256544502616},{"x":40.27777777777778,"y":52.80478683620045}],"accentMode":"gradient","accentGradient":{"backgroundMode":"linear","angle":183,"blend":100,"centerX":50,"centerY":50,"stops":["#5f7c65","#779861","#80d67a"],"weights":null,"positions":[44,77,100],"anchors":[{"x":15,"y":20},{"x":78,"y":70},{"x":50,"y":50}]},"stops":["#2B2724","#080906","#533E41","#674E50","#6E4B3C","#565355"]},"light":{"accent":"#9C6752","background":"#F4F4F4","foreground":"#171C19","panel":"#ECECEB","muted":"#393C3A","border":"#252421","hover":"#91604C","active":"#895B48","focus":"#9C6752","onAccent":"#FFFFFF","inputBackground":"#FBFBFB","inputForeground":"#171C19","inputBorder":"#252421","inputOpacity":100,"borderOpacity":100,"inputBorderOpacity":100,"navBackground":"#ECECEB","navSelected":"#CECFCE","navForeground":"#393C3A","navActiveForeground":"#171C19","navOpacity":86,"controlBackground":"#ECECEB","controlHover":"#D7D7D6","controlForeground":"#171C19","controlOpacity":100,"surfaceBackgroundMode":"solid","surfaceGradient":{"backgroundMode":"linear","angle":130,"blend":70,"centerX":50,"centerY":50,"stops":["#f5ede0","#d6e7df","#dfe5f5"],"weights":null,"positions":[0,50,100],"anchors":[{"x":10,"y":75},{"x":78,"y":70},{"x":50,"y":50}]},"backgroundMode":"linear","angle":90,"positions":[0,20,40,60,80,100],"weights":[45.411104368932044,40.50364077669904,7.827669902912623,2.6319781553398065,2.601638349514564,1.023968446601942],"centerX":50,"centerY":50,"blend":70,"anchors":[{"x":35.092592592592595,"y":6.507105459985041},{"x":52.5,"y":63.79955123410621},{"x":53.148148148148145,"y":56.99326851159312},{"x":57.68518518518518,"y":51.757666417352276},{"x":46.111111111111114,"y":41.361256544502616},{"x":40.27777777777778,"y":52.80478683620045}],"accentMode":"solid","accentGradient":{"backgroundMode":"linear","angle":120,"blend":70,"centerX":50,"centerY":50,"stops":["#82b895","#84b6d7","#b496d4"],"weights":null,"positions":[23,62,95],"anchors":[{"x":15,"y":20},{"x":78,"y":70},{"x":50,"y":50}]},"stops":["#A8A6A5","#A6A6A5","#ADA4A5","#B1A3A5","#BF9F93","#A8A6A8"]}},"surfaces":{"panel":{"plain":{"opacity":100,"blur":0,"refraction":0,"shadow":0,"border":1},"frosted":{"opacity":82,"blur":20,"refraction":0,"shadow":12,"border":1},"clear":{"opacity":32,"blur":11,"refraction":90,"shadow":12,"border":1}},"card":{"plain":{"opacity":100,"blur":0,"refraction":0,"shadow":0,"border":1},"frosted":{"opacity":82,"blur":20,"refraction":0,"shadow":12,"border":1},"clear":{"opacity":92,"blur":17,"refraction":89,"shadow":22,"border":1}}}},"layout":{"radii":{"input":8,"button":40,"card":23,"panel":29,"editor":20,"highlight":10,"tabs":28},"gap":21,"small":103,"tabs":"gooey","link":{"mode":"inverse","radius":6,"spread":3,"opacity":12,"duration":260,"color":"auto"},"units":{}},"imageSource":{"colors":[{"hex":"#080906","share":0.4050364077669903},{"hex":"#2B2724","share":0.45411104368932037},{"hex":"#6E5255","share":0.026319781553398057},{"hex":"#533E41","share":0.07827669902912622},{"hex":"#9C6752","share":0.02601638349514563},{"hex":"#5E5B5E","share":0.010239684466019418}],"primary":1,"accent":4,"relationship":"明暗对比","families":[{"name":"深灰与近黑","share":0.9374241504854369,"colors":["#080906","#2B2724","#533E41"]},{"name":"红与玫红","share":0.026319781553398057,"colors":["#6E5255"]},{"name":"陶土与橙褐","share":0.02601638349514563,"colors":["#9C6752"]},{"name":"中性灰","share":0.010239684466019418,"colors":["#5E5B5E"]}],"imageId":"609:01","name":"裂口陶器","method":"Oklab 最近候选色像素归属；透明像素按覆盖度计权","checks":[{"mode":"dark","text":15.729389938563084,"button":4.692189750018971,"input":14.000766080593783,"minimumBackground":7.0103836560016495},{"mode":"light","text":14.602017543535766,"button":4.692189750018971,"input":16.681090194975607,"minimumBackground":7.065635461388643}],"region":{"id":"full","label":"全图","bounds":[0,0,1,1]}}};const root=document.documentElement;const applyRecipe=(snapshot,theme="dark")=>{let style=document.getElementById('youyang-live-recipe');if(!style){style=document.createElement('style');style.id='youyang-live-recipe';document.head.append(style);}style.textContent=window.YeshanRecipeOutput.css(snapshot,theme);root.dataset.theme=theme;root.dataset.buttonStyle=snapshot.appearance.buttonStyle;};window.YouyangDesign={recipe,applyRecipe};let nav;const attach=()=>{const host=document.querySelector('.site-nav');if(host)nav=window.YeshanMotionTabs.mount(host,{mode:'navigation',selector:':scope > a',value:host.querySelector(':scope > [aria-current]')?String([...host.querySelectorAll(':scope > a')].indexOf(host.querySelector(':scope > [aria-current]'))):'',duration:240});window.YouyangMotionInventory.stamp();};attach();addEventListener('pagehide',()=>{nav?.destroy();nav=null;});addEventListener('pageshow',event=>{if(event.persisted&&!nav)attach();});})();
