const presets = {
  valid: {
    voiceJson: `{
  "Narrator": "Measured adult narrator, neutral and clear, steady pacing, clean diction, no background noise.",
  "Guide": "Warm middle-aged voice, calm and instructive, slightly low register, patient delivery, no background noise."
}`,
    dialogue: `[Narrator]: Rain tapped softly against the windows of the archive.
[Narrator]: A lantern flickered once, then steadied.
[Guide]: Keep your voice descriptions separate from your narration beats.
[Guide]: If a line feels too long, split it before you render it.`,
  },
  variants: {
    voiceJson: `{
  "Narrator": "Measured adult narrator, ominous and detached.",
  "Villain_Cold": "Old deep voice, cold and controlled.",
  "Villain_Bitter": "Old deep voice, bitter and cutting, but restrained.",
  "Villain_Angry": "Old deep voice, harsh and venomous, but not shouting."
}`,
    dialogue: `[Narrator]: Rain rattled against the stained glass.
[Villain_Cold]: "You speak of honor as if it is a shield."
[Narrator]: He circled the hero.
[Villain_Bitter]: "But tell me... what good does honor actually do?"
[Villain_Angry]: "You are not a saint. You are just pathetic."`,
  },
};

const pipelineSteps = [
  {
    id: "render",
    label: "Narrate dialogue",
    meta: "Primary render stage",
    description:
      "The main script parses bracketed speaker lines, generates or reuses character reference clips, then writes numbered WAV fragments plus a manifest file.",
    inputLine: "Input: dialogue.txt + characters.json",
    outputLine: "Output: numbered WAV files + manifest.csv + _character_references",
    command:
      "python narrate_dialogue.py samples\\inputs\\quickstart_dialogue.txt --characters samples\\inputs\\quickstart_characters.json --model-size 0.6B --output-dir output_quickstart --merge-output --merge-filename quickstart_merged.wav",
  },
  {
    id: "merge",
    label: "Merge fragments",
    meta: "Consolidate generated fragments",
    description:
      "Merge uses the manifest ordering and applies one pause value for same-speaker adjacency and another for speaker changes.",
    inputLine: "Input: output folder + manifest.csv",
    outputLine: "Output: merged WAV",
    command:
      "python merge_wavs.py output_villain_directed --out villain_directed_merged_tighter.wav --pause-ms 120 --speaker-change-pause-ms 220",
  },
  {
    id: "mp3",
    label: "Export MP3 (optional)",
    meta: "Compressed audio delivery",
    description:
      "MP3 export uses the bundled FFmpeg binary through pydub, making sharing and playback simpler than raw WAV.",
    inputLine: "Input: merged WAV",
    outputLine: "Output: MP3",
    command:
      "python convert_audio.py output_villain_directed\\villain_directed_merged_tighter.wav --output output_villain_directed\\villain_directed_merged_tighter.mp3 --bitrate 192k",
  },
  {
    id: "mp4",
    label: "Export MP4 (optional)",
    meta: "Video wrapper for sharing",
    description:
      "MP4 export wraps the audio in a still-image or solid-color video container using FFmpeg, which is useful for social posting and messaging apps.",
    inputLine: "Input: MP3 or merged WAV + optional image",
    outputLine: "Output: MP4",
    command:
      "python convert_audio_to_mp4.py output_villain_directed\\villain_directed_merged_tighter.mp3 --output output_villain_directed\\villain_directed_merged_tighter_image.mp4 --image output_villain_directed\\Gemini_Generated_Image_vf4vupvf4vupvf4v.png --size 1920x1080 --color black --fps 30 --audio-bitrate 192k",
  },
];

const artifacts = [
  {
    id: "references",
    label: "Character references",
    meta: "Cached voice anchors",
    description:
      "The _character_references folder stores reusable clips generated from the voice descriptions. It avoids redesigning the same voice on every run.",
    files: [
      "_character_references/",
      "_character_references/Narrator.wav",
      "_character_references/Villain_Cold.wav",
      "_character_references/Villain_Bitter.wav",
      "_character_references/Villain_Angry.wav",
    ],
    media: [
      {
        type: "audio",
        label: "Narrator reference",
        file: "Narrator.wav",
        src: "media/reference_Narrator.wav",
      },
      {
        type: "audio",
        label: "Villain cold reference",
        file: "Villain_Cold.wav",
        src: "media/reference_Villain_Cold.wav",
      },
    ],
    folderTree: [
      "output_villain_directed/",
      "  _character_references/",
      "    Narrator.wav",
      "    Villain_Cold.wav",
      "    Villain_Bitter.wav",
      "    Villain_Angry.wav",
    ],
  },
  {
    id: "fragments",
    label: "Numbered WAV fragments",
    meta: "Per-line or per-chunk narration",
    description:
      "Each dialogue line, or each split chunk from a long line, is written as an ordered WAV file such as 0001_Narrator.wav. This keeps synthesis load smaller and lets you regenerate individual lines if one performance is not acceptable.",
    files: ["0001_Narrator.wav", "0003_Villain_Cold.wav"],
    media: [
      {
        type: "audio",
        label: "Narrator fragment",
        file: "0001_Narrator.wav",
        src: "media/0001_Narrator.wav",
      },
      {
        type: "audio",
        label: "Villain fragment",
        file: "0003_Villain_Cold.wav",
        src: "media/0003_Villain_Cold.wav",
      },
    ],
  },
  {
    id: "manifest",
    label: "Manifest CSV",
    meta: "The index of generated speech",
    description:
      "The manifest is the authoritative map between line index, character, original text, and fragment filename. Merge relies on this ordering.",
    files: ["manifest.csv"],
    showManifest: true,
  },
  {
    id: "merged",
    label: "Merged delivery files",
    meta: "WAV, MP3, and MP4",
    description:
      "The shareable outputs are derived artifacts. WAV keeps the highest fidelity, MP3 is convenient for playback, and MP4 is useful for video-first platforms.",
    files: ["villain_directed_merged.wav", "villain_directed_merged.mp3", "villain_directed_merged.mp4"],
    media: [
      {
        type: "audio",
        label: "WAV preview",
        file: "villain_directed_merged.wav",
        src: "media/villain_directed_merged.wav",
      },
      {
        type: "audio",
        label: "MP3 preview",
        file: "villain_directed_merged.mp3",
        src: "media/villain_directed_merged.mp3",
      },
      {
        type: "video",
        label: "MP4 preview",
        file: "villain_directed_merged_image.mp4",
        src: "media/villain_directed_merged_image.mp4",
      },
    ],
  },
];

const manifestRows = [
  {
    index: "1",
    character: "Narrator",
    text: "The rain lashed against the cathedral's stained glass, casting fractured, bloody patterns across the villain's face.",
    file: "0001_Narrator.wav",
  },
  {
    index: "3",
    character: "Villain_Cold",
    text: "\"You speak of honor as if it is a shield.\"",
    file: "0003_Villain_Cold.wav",
  },
  {
    index: "8",
    character: "Villain_Bitter",
    text: "\"Does it not take a more jagged kind of courage to give away a redeeming quality?\"",
    file: "0008_Villain_Bitter.wav",
  },
  {
    index: "12",
    character: "Villain_Angry",
    text: "\"No. You have not.\"",
    file: "0012_Villain_Angry.wav",
  },
];

const voiceEditor = document.querySelector("#voice-editor");
const dialogueEditor = document.querySelector("#dialogue-editor");
const presetSelect = document.querySelector("#preset-select");
const pipelineStepsNode = document.querySelector("#pipeline-steps");
const pipelineDetailNode = document.querySelector("#pipeline-detail");
const artifactListNode = document.querySelector("#artifact-list");
const artifactDetailNode = document.querySelector("#artifact-detail");

function applyPreset(name) {
  const preset = presets[name];
  voiceEditor.value = preset.voiceJson;
  dialogueEditor.value = preset.dialogue;
}

function renderPipeline(activeId = pipelineSteps[0].id) {
  pipelineStepsNode.innerHTML = pipelineSteps
    .map(
      (step) => `
        <button class="step-button ${step.id === activeId ? "active" : ""}" data-step-id="${step.id}">
          <span class="step-label">${step.label}</span>
          <span class="step-meta">${step.meta}</span>
        </button>`
    )
    .join("");

  const active = pipelineSteps.find((step) => step.id === activeId);
  pipelineDetailNode.innerHTML = `
    <div class="detail-top">
      <h3>${active.label}</h3>
      <span class="badge">${active.meta}</span>
    </div>
    <p class="pipeline-meta">${active.description}</p>
    <div class="info-lines">
      <div class="info-line">${active.inputLine}</div>
      <div class="info-line">${active.outputLine}</div>
    </div>
    <span class="detail-label">Command</span>
    <code>${active.command}</code>
  `;

  pipelineStepsNode.querySelectorAll(".step-button").forEach((button) => {
    button.addEventListener("click", () => renderPipeline(button.dataset.stepId));
  });
}

function renderArtifacts(activeId = artifacts[0].id) {
  artifactListNode.innerHTML = artifacts
    .map(
      (artifact) => `
        <button class="artifact-button ${artifact.id === activeId ? "active" : ""}" data-artifact-id="${artifact.id}">
          <span class="artifact-label">${artifact.label}</span>
          <span class="artifact-meta">${artifact.meta}</span>
        </button>`
    )
    .join("");

  const active = artifacts.find((artifact) => artifact.id === activeId);
  const mediaMarkup = (active.media || [])
    .map((item) => {
      if (item.type === "video") {
        return `
          <div class="media-card">
            <div class="media-label-row">
              <span class="media-label">${item.label}</span>
              <span class="file-chip">${item.file}</span>
            </div>
            <div class="media-frame">
              <video controls preload="metadata" src="${item.src}"></video>
            </div>
          </div>`;
      }

      if (item.type === "audio") {
        return `
          <div class="media-card">
            <div class="media-label-row">
              <span class="media-label">${item.label}</span>
              <span class="file-chip">${item.file}</span>
            </div>
            <audio controls preload="metadata" src="${item.src}"></audio>
          </div>`;
      }

      return `
        <div class="media-card">
          <div class="media-label-row">
            <span class="media-label">${item.label}</span>
            <span class="file-chip">${item.file}</span>
          </div>
          <pre class="folder-tree">${item.lines.join("\n")}</pre>
        </div>`;
    })
    .join("");

  const treeMarkup = active.folderTree
    ? `
      <div class="media-card">
        <div class="media-label-row">
          <span class="media-label">Folder structure</span>
          <span class="file-chip">_character_references</span>
        </div>
        <pre class="folder-tree">${active.folderTree.join("\n")}</pre>
      </div>`
    : "";

  const manifestMarkup = active.showManifest
    ? `
      <div class="manifest-block">
        <div class="editor-heading">
          <h3>Manifest sample</h3>
          <span class="file-chip">manifest.csv</span>
        </div>
        <p class="manifest-copy">
          The manifest tracks line order, character attribution, text, and the WAV filename for each generated fragment.
        </p>
        <div class="manifest-table-wrap">
          <table>
            <thead>
              <tr>
                <th>Index</th>
                <th>Character</th>
                <th>Text</th>
                <th>File</th>
              </tr>
            </thead>
            <tbody>
              ${manifestRows
                .map(
                  (row) => `
                    <tr>
                      <td>${row.index}</td>
                      <td>${row.character}</td>
                      <td>${row.text}</td>
                      <td>${row.file}</td>
                    </tr>`
                )
                .join("")}
            </tbody>
          </table>
        </div>
      </div>`
    : "";

  artifactDetailNode.innerHTML = `
    <div class="detail-top">
      <h3>${active.label}</h3>
      <span class="badge">${active.meta}</span>
    </div>
    <p class="artifact-meta">${active.description}</p>
    <div class="chip-row">
      ${active.files.map((item) => `<span class="chip">${item}</span>`).join("")}
    </div>
    ${mediaMarkup || treeMarkup ? `<div class="media-stack">${mediaMarkup}${treeMarkup}</div>` : ""}
    ${manifestMarkup}
  `;

  artifactListNode.querySelectorAll(".artifact-button").forEach((button) => {
    button.addEventListener("click", () => renderArtifacts(button.dataset.artifactId));
  });
}

presetSelect.addEventListener("change", () => applyPreset(presetSelect.value));

applyPreset("valid");
renderPipeline();
renderArtifacts();
