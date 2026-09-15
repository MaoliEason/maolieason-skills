import { readFile, readdir } from "node:fs/promises";
import { join } from "node:path";

const root = new URL("../skills/", import.meta.url);
const entries = (await readdir(root, { withFileTypes: true })).filter((entry) => entry.isDirectory());
if (!entries.length) throw new Error("No skills found");

const forbidden = [
  /BEGIN (RSA |OPENSSH )?PRIVATE KEY/,
  /CLOUDFLARE_API_TOKEN\s*=/i,
  /GITHUB_TOKEN\s*=/i,
  /DATABASE_URL\s*=/i,
  /api[_-]?key\s*[:=]\s*["'][^"'\s]+/i,
];

for (const entry of entries) {
  const directory = join(root.pathname, entry.name);
  const skill = await readFile(join(directory, "SKILL.md"), "utf8");
  const agent = await readFile(join(directory, "agents/openai.yaml"), "utf8");
  if (!skill.startsWith("---\nname: ")) throw new Error(`${entry.name}: invalid SKILL.md frontmatter`);
  if (!skill.includes(`name: ${entry.name}\n`)) throw new Error(`${entry.name}: folder and skill name differ`);
  if (!/^---\nname: [a-z0-9-]+\ndescription: .+\n---\n/s.test(skill)) throw new Error(`${entry.name}: name and description are required`);
  if (!agent.includes(`$${entry.name}`)) throw new Error(`${entry.name}: default prompt must mention the skill`);
  const files = await readdir(directory, { recursive: true });
  for (const file of files) {
    const path = join(directory, file);
    try {
      const content = await readFile(path, "utf8");
      for (const pattern of forbidden) if (pattern.test(content)) throw new Error(`${entry.name}/${file}: possible secret`);
    } catch (error) {
      if (error?.code !== "EISDIR") throw error;
    }
  }
}

console.log(`Validated ${entries.length} skills`);

