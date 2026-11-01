# General scientific principles (apply to every project)
Starter list. Edit freely; project standards in reference/golden_standard/ take precedence.

1. **No leakage**: split train/validation/test before any fitting, scaling, feature selection, or tuning; fit transforms on training data only.
2. **Replicates**: conclusions need biological/independent replicates, not just technical ones; report n.
3. **Multiple testing**: when testing many hypotheses, report adjusted p-values (FDR/Bonferroni) and state the method.
4. **Reproducibility**: record random seeds, software versions, and exact parameters with each result.
5. **Baselines**: compare against a simple baseline and report effect sizes with uncertainty, not p-values alone.
6. **Raw data is read-only**: never modify inputs in place; derive new files and keep the processing steps scripted.
7. **Labels**: document how labels were produced; check class balance; keep label sources separate from features.
8. **Sanity before scale**: inspect distributions, missingness, and outliers before modeling; too-perfect results are suspect.
