; ============================================================
; installer.iss
; Inno Setup 6 script — ISO Manual Assistant
;
; Produces:  dist\ISO_Manual_Assistant_Setup_v1.0.0.exe
;
; What it does:
;   1. Copies the PyInstaller bundle into Program Files
;   2. Creates a Start-menu shortcut and optional desktop icon
;   3. Shows a model-selection page (checkboxes)
;   4. Post-install: downloads Ollama if not present, starts it,
;      then pulls each selected model via "ollama pull"
;   5. Copies pre-built ChromaDB vector index to
;      %APPDATA%\ISO Manual Assistant\data\vector_db\
;      (chat history and documents are NOT copied — fresh per user)
; ============================================================

#define AppName      "ISO Manual Assistant"
#define AppVersion   "1.0.0"
#define AppPublisher "ISO Assist"
#define AppExeName   "ISO_Manual_Assistant.exe"
#define AppDataDir   "{userappdata}\ISO Manual Assistant"
#define BundleDir    "..\dist\ISO_Manual_Assistant"
#define VectorDbDir  "..\data\vector_db"

[Setup]
AppId={{8F2A1B3C-4D5E-6F7A-8B9C-0D1E2F3A4B5C}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL=https://github.com/your-org/iso-manual-assistant
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes
OutputDir=..\dist
OutputBaseFilename=ISO_Manual_Assistant_Setup_v{#AppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
; No admin required — installs to per-user AppData + optional Program Files
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
WizardStyle=modern
WizardResizable=yes
; Show a larger wizard so the model list is readable
WizardImageFile=compiler:WizModernImage.bmp
WizardSmallImageFile=compiler:WizModernSmallImage.bmp
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#AppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

; ── Files ─────────────────────────────────────────────────────────────────────

[Files]
; PyInstaller bundle — the full app
Source: "{#BundleDir}\*"; \
  DestDir: "{app}"; \
  Flags: ignoreversion recursesubdirs createallsubdirs

; Pre-built ChromaDB vector index (only if it exists at build time)
; Installed into the user's APPDATA so the app can write to it.
; Chat history (chats.db) and documents are intentionally excluded.
Source: "{#VectorDbDir}\*"; \
  DestDir: "{userappdata}\{#AppName}\data\vector_db"; \
  Flags: ignoreversion recursesubdirs createallsubdirs skipifsourcedoesntexist

; ── Icons / shortcuts ─────────────────────────────────────────────────────────

[Icons]
Name: "{group}\{#AppName}";          Filename: "{app}\{#AppExeName}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}";    Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

; ── Registry — write data dir so the app can find it if needed ────────────────

[Registry]
Root: HKCU; Subkey: "Software\{#AppName}"; ValueType: string; \
  ValueName: "DataDir"; \
  ValueData: "{userappdata}\{#AppName}"; \
  Flags: createvalueifdoesntexist

; ── Pascal scripting ──────────────────────────────────────────────────────────

[Code]

// ── State ────────────────────────────────────────────────────────────────────
var
  // Model-selection wizard page
  ModelPage    : TWizardPage;
  ModelListBox : TNewCheckListBox;
  ModelNote    : TNewStaticText;

  // Checkbox indices
  IdxNomic   : Integer;
  IdxQwen25  : Integer;
  IdxQwen3   : Integer;
  IdxGemma3  : Integer;
  IdxLlama31 : Integer;

// ── Helpers ──────────────────────────────────────────────────────────────────

function OllamaExePath: String;
begin
  // Check known install locations in priority order
  if FileExists(ExpandConstant('{localappdata}\Programs\Ollama\ollama.exe')) then
    Result := ExpandConstant('{localappdata}\Programs\Ollama\ollama.exe')
  else if FileExists(ExpandConstant('{pf64}\Ollama\ollama.exe')) then
    Result := ExpandConstant('{pf64}\Ollama\ollama.exe')
  else if FileExists(ExpandConstant('{pf}\Ollama\ollama.exe')) then
    Result := ExpandConstant('{pf}\Ollama\ollama.exe')
  else
    Result := 'ollama';  // rely on PATH
end;

function OllamaInstalled: Boolean;
begin
  Result :=
    FileExists(ExpandConstant('{localappdata}\Programs\Ollama\ollama.exe')) or
    FileExists(ExpandConstant('{pf64}\Ollama\ollama.exe')) or
    FileExists(ExpandConstant('{pf}\Ollama\ollama.exe'));
end;

procedure UpdateStatus(const Msg: String);
begin
  WizardForm.StatusLabel.Caption := Msg;
  WizardForm.StatusLabel.Update;
end;

// ── Model-selection wizard page ───────────────────────────────────────────────

procedure InitializeWizard;
begin
  ModelPage := CreateCustomPage(
    wpSelectTasks,
    'Select AI Models',
    'Choose which language models to install. ' +
    'Models are stored locally — no internet required after download.'
  );

  // Checkbox list
  ModelListBox := TNewCheckListBox.Create(WizardForm);
  ModelListBox.Parent := ModelPage.Surface;
  ModelListBox.Left   := 0;
  ModelListBox.Top    := 8;
  ModelListBox.Width  := ModelPage.SurfaceWidth;
  ModelListBox.Height := 188;
  ModelListBox.Flat   := True;

  // nomic-embed-text is always required (disabled, pre-checked)
  IdxNomic   := ModelListBox.AddCheckBox(
    'nomic-embed-text    [REQUIRED]  —  Embedding / knowledge-base search  (~270 MB)',
    '', 0, True, False, False, True, nil);

  IdxQwen25  := ModelListBox.AddCheckBox(
    'Qwen 2.5 – 7B    [Recommended]  —  Best accuracy/speed balance  (~4.5 GB)',
    '', 0, True, True, False, True, nil);

  IdxQwen3   := ModelListBox.AddCheckBox(
    'Qwen 3 – 8B    —  Latest Qwen model with extended reasoning  (~5 GB)',
    '', 0, False, True, False, True, nil);

  IdxGemma3  := ModelListBox.AddCheckBox(
    'Gemma 3 – 4B    —  Google''s lightweight model, fastest responses  (~2.5 GB)',
    '', 0, False, True, False, True, nil);

  IdxLlama31 := ModelListBox.AddCheckBox(
    'Llama 3.1 – 8B    —  Meta''s open-source model  (~4.7 GB)',
    '', 0, False, True, False, True, nil);

  // Footer note
  ModelNote := TNewStaticText.Create(WizardForm);
  ModelNote.Parent   := ModelPage.Surface;
  ModelNote.Left     := 0;
  ModelNote.Top      := ModelListBox.Top + ModelListBox.Height + 10;
  ModelNote.Width    := ModelPage.SurfaceWidth;
  ModelNote.AutoSize := False;
  ModelNote.Height   := 60;
  ModelNote.WordWrap := True;
  ModelNote.Caption  :=
    'Tip: You can download additional models later from inside the app.' + #13#10 +
    'Models are pulled from Ollama (ollama.com) and stored in your ' +
    'user profile — they are never uploaded anywhere.' + #13#10 +
    'Total download size for all models: ~17 GB.';
end;

// Prevent advancing past model page without at least one LLM selected
function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if CurPageID = ModelPage.ID then begin
    if not (ModelListBox.Checked[IdxQwen25]  or
            ModelListBox.Checked[IdxQwen3]   or
            ModelListBox.Checked[IdxGemma3]  or
            ModelListBox.Checked[IdxLlama31]) then
    begin
      MsgBox(
        'Please select at least one language model (LLM).' + #13#10 +
        'You need an LLM to chat with your documents.',
        mbInformation, MB_OK
      );
      Result := False;
    end;
  end;
end;

// ── Post-install: Ollama setup + model downloads ──────────────────────────────

procedure DownloadAndInstallOllama;
var
  TempSetup  : String;
  ResultCode : Integer;
begin
  UpdateStatus('Downloading Ollama installer…  (this may take a moment)');

  TempSetup := ExpandConstant('{tmp}\OllamaSetup.exe');

  // Download via PowerShell (TLS 1.2 forced for older Windows)
  Exec(
    'powershell.exe',
    '-NoProfile -ExecutionPolicy Bypass -Command "' +
    '[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; ' +
    'Invoke-WebRequest -Uri ''https://ollama.com/download/OllamaSetup.exe'' ' +
    '-OutFile ''' + TempSetup + ''' -UseBasicParsing"',
    '',
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode
  );

  if not FileExists(TempSetup) then begin
    MsgBox(
      'Could not download Ollama.' + #13#10 +
      'Please install it manually from https://ollama.com then rerun the setup.',
      mbError, MB_OK
    );
    Exit;
  end;

  UpdateStatus('Installing Ollama…');
  Exec(TempSetup, '/VERYSILENT /NORESTART', '', SW_SHOW, ewWaitUntilTerminated, ResultCode);
  Sleep(2000);
end;

procedure EnsureOllamaRunning;
var
  ResultCode : Integer;
  ExePath    : String;
begin
  ExePath := OllamaExePath;
  UpdateStatus('Starting Ollama service…');
  ShellExec('open', ExePath, 'serve', '', SW_HIDE, ewNoWait, ResultCode);
  Sleep(4000);  // give the server time to bind
end;

procedure PullOneModel(const ModelId, DisplayName: String; Current, Total: Integer);
var
  ResultCode : Integer;
  ProgressPct: Integer;
begin
  ProgressPct := ((Current - 1) * 100) div Total;
  WizardForm.ProgressGauge.Position := ProgressPct;
  UpdateStatus(
    Format('Downloading model %d of %d:  %s', [Current, Total, DisplayName]) +
    #13#10 + '  (this can take several minutes — please wait)'
  );
  Exec(
    OllamaExePath,
    'pull ' + ModelId,
    '',
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode
  );
  if ResultCode <> 0 then
    MsgBox(
      'Warning: failed to download ' + DisplayName + '.' + #13#10 +
      'You can download it later from inside the app.',
      mbInformation, MB_OK
    );
end;

// Main post-install hook
procedure CurStepChanged(CurStep: TSetupStep);
var
  Total, Current : Integer;
begin
  if CurStep <> ssPostInstall then
    Exit;

  // ── 1. Ensure Ollama is installed ─────────────────────────────────────────
  if not OllamaInstalled then
    DownloadAndInstallOllama;

  // ── 2. Start Ollama service ───────────────────────────────────────────────
  EnsureOllamaRunning;

  // ── 3. Count models to pull ───────────────────────────────────────────────
  Total := 1;  // nomic-embed-text is always included
  if ModelListBox.Checked[IdxQwen25]  then Inc(Total);
  if ModelListBox.Checked[IdxQwen3]   then Inc(Total);
  if ModelListBox.Checked[IdxGemma3]  then Inc(Total);
  if ModelListBox.Checked[IdxLlama31] then Inc(Total);

  WizardForm.ProgressGauge.Max      := 100;
  WizardForm.ProgressGauge.Position := 0;

  Current := 1;

  // ── 4. Pull models ────────────────────────────────────────────────────────
  PullOneModel('nomic-embed-text', 'nomic-embed-text  (embedding)', Current, Total);
  Inc(Current);

  if ModelListBox.Checked[IdxQwen25] then begin
    PullOneModel('qwen2.5:7b', 'Qwen 2.5 – 7B', Current, Total);
    Inc(Current);
  end;
  if ModelListBox.Checked[IdxQwen3] then begin
    PullOneModel('qwen3:8b', 'Qwen 3 – 8B', Current, Total);
    Inc(Current);
  end;
  if ModelListBox.Checked[IdxGemma3] then begin
    PullOneModel('gemma3:4b', 'Gemma 3 – 4B', Current, Total);
    Inc(Current);
  end;
  if ModelListBox.Checked[IdxLlama31] then begin
    PullOneModel('llama3.1:8b', 'Llama 3.1 – 8B', Current, Total);
  end;

  WizardForm.ProgressGauge.Position := 100;
  UpdateStatus('All models downloaded successfully!');
end;
