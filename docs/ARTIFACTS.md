# Academic documents

The report and presentation PDF compile from actual LaTeX sources. The report follows the reference's numbered section structure, serif typography, contents, tables, diagrams and page numbering. All its figures use grayscale. The deck follows the reference's navy heading bar, teal bullets and orange explanation blocks. Both omit a title page as requested.

## Edit and compile

Open report/report.tex or presentation/presentation.tex in a LaTeX editor. Sources require standard LaTeX packages and the image files under assets/. From the relevant source directory, run `tectonic report.tex` or `tectonic presentation.tex`. A conventional LaTeX installation can compile the same sources; rerun as needed to resolve contents and references.

The sources use relative paths. Keep docs/assets beside the report and presentation folders. Add a title page in the source if desired, then regenerate contents/page numbers. The presentation currently contains exactly ten content frames. Inserting a cover increases the total to eleven unless an existing frame is replaced.

## Editable PowerPoint

The PPTX contains editable text, native tables and a native connected architecture diagram. Dashboard charts remain original screenshots as requested. It uses Arial for compatibility, while the LaTeX PDF uses Latin Modern. The PDFs and PPTX have matching findings and analytical scope, with small layout differences between the two formats.

build.mjs is the presentation authoring source for the Codex bundled @oai/artifact-tool runtime. It is not required to run the dashboard. It deliberately refuses to overwrite an existing finalized output. To rebuild a revision, choose a new output filename in the script and configure RUNTIME_NODE_MODULES to the bundled Node package directory before running it. The application itself needs only requirements.txt, its private credentials and the existing BigQuery tables.

## Evidence and attribution

Dashboard screenshots show executed BigQuery results for 2024. All-states PM2.5 captures use 75% coverage, 10% monthly high days and three high months. Combined captures use the same screening thresholds and the separate Poor-or-worse day definition. Images retain their legends and relevant map attribution. Crops remove surrounding browser/UI whitespace. Grayscale copies support the report's print format.

Numerical tables come from output/india/ exports and data/india/audit/ run records. Three external references appear in each final document. Source credentials, original data files and development caches are not part of the Git repository.
