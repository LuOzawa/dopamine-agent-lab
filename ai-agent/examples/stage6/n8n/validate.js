return $input.all().map(item => {
  let raw = item.json.modelText;
  if (raw === undefined) raw = (item.json.output || []).flatMap(x => x.content || []).filter(x => x.type === 'output_text').map(x => x.text).join('');
  try {
    const value = JSON.parse(raw);
    if (!value || typeof value.summary !== 'string' || !value.summary.trim() || value.summary.length > 1000) throw new Error('summary must be a nonempty string <= 1000 chars');
    return {json: {case: item.json.case || 'webhook', ok: true, summary: value.summary}};
  } catch (_) {
    return {json: {case: item.json.case || 'webhook', ok: false, summary: '生成结果格式错误，请稍后重试。'}};
  }
});
