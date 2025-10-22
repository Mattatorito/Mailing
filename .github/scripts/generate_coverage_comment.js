#!/usr/bin/env node
/**
 * Generate PR comment with coverage information.
 */

const fs = require('fs');

function main() {
  try {
    const coverage = JSON.parse(fs.readFileSync('coverage.json', 'utf8'));
    
    // Validate coverage data structure
    if (!coverage.totals || typeof coverage.totals.percent_covered !== 'number') {
      throw new Error('Invalid coverage data: missing or invalid totals.percent_covered');
    }
    
    const total = coverage.totals.percent_covered.toFixed(2);
    const threshold = process.env.COVERAGE_THRESHOLD || '90';
    
    // Validate and process files data
    let filesSection = '';
    if (coverage.files && Object.keys(coverage.files).length > 0) {
      filesSection = `### Coverage by Module:
${Object.entries(coverage.files)
  .filter(([file, data]) => data && data.summary && typeof data.summary.percent_covered === 'number')
  .map(([file, data]) => `- \`${file}\`: ${data.summary.percent_covered.toFixed(1)}%`)
  .slice(0, 10)
  .join('\n')}`;
    } else {
      filesSection = '### Coverage by Module:\nNo detailed file coverage available.';
    }
    
    const comment = `## 📊 Coverage Report
    
**Total Coverage:** ${total}%
**Threshold:** ${threshold}%
**Status:** ${total >= threshold ? '✅ PASS' : '❌ FAIL'}

${filesSection}

[View detailed coverage report](https://github.com/${process.env.GITHUB_REPOSITORY}/actions/runs/${process.env.GITHUB_RUN_ID})`;

    console.log(comment);
    
    // Save comment to file for GitHub Actions
    fs.writeFileSync('coverage-comment.txt', comment);
    
  } catch (error) {
    console.error('Error generating coverage comment:', error);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}