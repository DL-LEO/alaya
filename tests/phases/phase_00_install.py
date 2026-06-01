"""Phase 00: Installation (T+0).

Checks that the alaya package has a complete, valid file structure before any
configuration or use.  This is the "fresh clone" state.
"""

import json
import os

from phases.base_phase import BasePhase


class Phase00(BasePhase):
    """Installation integrity checks."""

    REQUIRED_DIRS = ["manas", "scripts", "scripts/lib", "templates", "docs", "config"]
    REQUIRED_FILES = [
        "SKILL.md", "README.md", "CHANGELOG.md", "LICENSE", "requirements.txt",
        "config/default_config.json",
        "templates/persona_template.json",
        "templates/persona_profile_template.md",
        "docs/quick-start.md", "docs/role-guide.md",
        "scripts/setup_wizard.py", "scripts/build_index.py",
        "scripts/perfume.py", "scripts/perfume_knowledge.py",
        "scripts/perfume_memory.py", "scripts/perfume_persona.py",
        "scripts/batch_import.py", "scripts/import_paper.py",
        "scripts/health_check.py", "scripts/fix_links.py",
        "scripts/bi_observer.py", "scripts/persona_manager.py",
        "scripts/lib/__init__.py", "scripts/lib/yaml_utils.py",
        "scripts/lib/format_converter.py",
    ]

    REQUIRED_MANAS_JSON = [
        "feynman", "socrates", "buddha", "zhuangzi",
        "carl_jung", "galileo", "audrey_hepburn", "xiaozhao",
    ]
    REQUIRED_MANAS_PROFILE = [f"{name}_profile" for name in REQUIRED_MANAS_JSON]

    def __init__(self, log, kb):
        super().__init__("phase_00", "安装完整性检查 (T+0)", log, kb)

    def setup(self):
        pass  # No setup needed — checking the template copy

    def run_all(self):
        self._check_directories()
        self._check_files()
        self._check_json_validity()
        self._check_manas_pairs()
        self._check_skill_frontmatter()

    def _check_directories(self):
        for d in self.REQUIRED_DIRS:
            path = os.path.join(self.kb.workdir, d)
            self._check_file(f"C-00-{self.REQUIRED_DIRS.index(d):02d}", path, should_exist=True)

    def _check_files(self):
        for fname in self.REQUIRED_FILES:
            path = os.path.join(self.kb.workdir, fname)
            self._check_file(f"C-00-f{self.REQUIRED_FILES.index(fname):02d}", path, should_exist=True)

    def _check_json_validity(self):
        """Validate all JSON files are parseable."""
        json_files = []
        for root, dirs, files in os.walk(self.kb.workdir):
            for fn in files:
                if fn.endswith(".json"):
                    json_files.append(os.path.join(root, fn))

        for fpath in json_files:
            rel = os.path.relpath(fpath, self.kb.workdir)
            rid = f"C-00-json{json_files.index(fpath):02d}"
            # Check encoding first
            with open(fpath, "rb") as f:
                raw = f.read()
            if raw[:3] == b'\xef\xbb\xbf':
                self._warn(rid, "json_valid", "file_integrity", rel,
                           expected="UTF-8 without BOM",
                           actual="UTF-8 with BOM detected",
                           detail=f"{rel} has UTF-8 BOM — may cause parsing issues",
                           suggestion="Save as UTF-8 without BOM")
            try:
                with open(fpath, encoding="utf-8") as f:
                    json.load(f)
                self._pass(rid + "-parse", "json_valid", "file_integrity", rel,
                           detail="valid JSON")
            except json.JSONDecodeError as e:
                self._fail(rid + "-parse", "json_valid", "file_integrity", rel,
                           expected="valid JSON", actual=f"parse error: {e}",
                           detail=f"File: {rel}, line {e.lineno}, col {e.colno}: {e.msg}",
                           suggestion=f"Fix the JSON syntax at {rel}:{e.lineno}")

    def _check_manas_pairs(self):
        """Verify each persona has BOTH a .json and a _profile.md."""
        manas_dir = os.path.join(self.kb.workdir, "manas")
        if not os.path.isdir(manas_dir):
            self._fail("C-00-manas", "dir_exists", "file_integrity", "manas/",
                       expected="manas/ directory exists", actual="not found")
            return

        for name in self.REQUIRED_MANAS_JSON:
            json_path = os.path.join(manas_dir, f"{name}.json")
            profile_path = os.path.join(manas_dir, f"{name}_profile.md")
            cid = f"C-00-mana-{self.REQUIRED_MANAS_JSON.index(name):02d}"
            json_ok = os.path.exists(json_path)
            prof_ok = os.path.exists(profile_path)
            if json_ok and prof_ok:
                self._pass(cid, "file_exists", "file_integrity", f"manas/{name}.json + _profile.md",
                           detail="both files present")
            else:
                missing = []
                if not json_ok:
                    missing.append(f"{name}.json")
                if not prof_ok:
                    missing.append(f"{name}_profile.md")
                self._fail(cid, "file_exists", "file_integrity", f"manas/{name}",
                           expected="both .json and _profile.md exist",
                           actual=f"missing: {', '.join(missing)}",
                           detail=f"Persona '{name}' has incomplete files in manas/",
                           suggestion=f"Create the missing file(s): {', '.join(missing)}")

    def _check_skill_frontmatter(self):
        """Check SKILL.md has valid frontmatter with required fields."""
        skill_path = os.path.join(self.kb.workdir, "SKILL.md")
        if not os.path.exists(skill_path):
            self._fail("C-00-skill", "file_exists", "file_integrity", "SKILL.md",
                       expected="SKILL.md exists", actual="not found")
            return

        with open(skill_path, encoding="utf-8") as f:
            raw = f.read()

        if not raw.startswith("---"):
            self._fail("C-00-skill-fm", "yaml_frontmatter", "file_integrity", "SKILL.md",
                       expected="frontmatter delimited by ---", actual="no leading ---",
                       suggestion="Add '---\\nname: Alaya\\ndescription: ...\\n---\\n' at the top")
            return

        end = raw.find("---", 3)
        if end < 0:
            self._fail("C-00-skill-fm", "yaml_frontmatter", "file_integrity", "SKILL.md",
                       expected="closing --- delimiter", actual="not found",
                       suggestion="Add '---' to close the frontmatter")
            return

        # Check essential fields
        yaml_str = raw[3:end]
        required_fields = ["name", "description", "version"]
        missing = []
        for field in required_fields:
            if f"{field}:" not in yaml_str:
                missing.append(field)

        if missing:
            self._fail("C-00-skill-fields", "yaml_frontmatter", "file_integrity", "SKILL.md",
                       expected=f"frontmatter fields: {required_fields}",
                       actual=f"missing: {missing}",
                       detail=f"YAML frontmatter snippet:\n{yaml_str[:200]}",
                       suggestion=f"Add missing field(s) to SKILL.md frontmatter: {missing}")
        else:
            self._pass("C-00-skill-fields", "yaml_frontmatter", "file_integrity", "SKILL.md",
                       detail="all required frontmatter fields present")

    def _check_gitignore(self):
        """Check .gitignore excludes runtime data."""
        gitignore_path = os.path.join(self.kb.workdir, ".gitignore")
        if not os.path.exists(gitignore_path):
            self._warn("C-00-gitignore", "file_exists", "file_integrity", ".gitignore",
                       expected=".gitignore exists", actual="not found",
                       detail="Missing .gitignore — runtime artifacts may be committed",
                       suggestion="Create .gitignore with entries for alaya/ runtime data")
            return

        with open(gitignore_path, encoding="utf-8") as f:
            content = f.read()

        runtime_patterns = ["alaya/", "wiki/", "*.checkpoint"]
        missing_patterns = [p for p in runtime_patterns if p not in content]
        if missing_patterns:
            self._warn("C-00-gitignore-pats", "file_exists", "file_integrity", ".gitignore",
                       expected=f"patterns in .gitignore: {runtime_patterns}",
                       actual=f"missing: {missing_patterns}",
                       detail="Runtime data dirs not excluded from version control",
                       suggestion=f"Add to .gitignore:\n{'  '.join(missing_patterns)}")
        else:
            self._pass("C-00-gitignore-pats", "file_exists", "file_integrity", ".gitignore",
                       detail="runtime patterns excluded")
