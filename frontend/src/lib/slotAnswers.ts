/** Client-side fallback when API omits slot_answers (e.g. stale backend). */

export function inferSlotAnswers(template: string, prompt: string): string[] {
  const nameMatch = prompt.match(/name='([^']+)'/);
  const ageMatch = prompt.match(/age=(\d+)/);
  if (nameMatch && ageMatch && template.includes('name = ___')) {
    return [`'${nameMatch[1]}'`, ageMatch[1], `f'{name} is {age} years old'`];
  }

  if (template.includes('print(___)') && template.split('___').length === 2) {
    const stdoutMatch = prompt.match(/print: '([^']+)'/i) || prompt.match(/'([^']+)'$/);
    if (stdoutMatch) {
      const word = stdoutMatch[1].split(' ').pop();
      if (word && /^[A-Za-z0-9]+$/.test(word)) {
        return [`'${word}'`];
      }
    }
  }

  return [];
}

export function assembleTemplate(template: string, slotAnswers: string[]): string {
  let i = 0;
  return template.replace(/___/g, () => slotAnswers[i++] ?? '');
}
