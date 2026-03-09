"""
Resolver Registry — defines the ordered list of resolvers for the
standard normalization pipeline.

Resolver ordering is significant:

  1.  BOMResolver              Fix column name corruption first — before any
                               other resolver reads column names.
  2.  BlankColumnResolver      Remove useless columns early — reduces work for
                               every subsequent step.
  3.  BlankRowResolver         Remove useless rows early — same rationale.
  4.  HeaderNormalizerResolver Normalize column names. This step intentionally
                               runs BEFORE duplicate detection because
                               normalization can create duplicates
                               (e.g. "Project Score" and "Project_Score" both
                               become "project_score").
  5.  DuplicateColumnResolver  Deduplicate AFTER normalization so that all
                               post-normalization collisions are caught.
  6.  BooleanResolver          Encoding: boolean text → 0/1.
  7.  LikertScaleResolver      Encoding: Likert text → 1–5.
  8.  PercentResolver          Encoding: "45%" → 0.45.
  9.  NumericTextResolver      Encoding: numeric strings → numeric dtype.
  10. MissingValueResolver     Encoding: NA/null strings → NaN.
  11. MultiRowHeaderResolver   Survey: collapse metadata first-row into column
                               names before any column-value resolvers run.
  12. MultiSelectResolver      Survey: expand semicolon/pipe multi-select cells
                               into binary indicator columns.
  13. DelimitedListResolver    Survey: expand comma-list cells into binary
                               indicator columns.
  14. CarryForwardResolver     Survey: routing-artifact strings → NaN.
"""
from typing import List

from app.resolvers.base_resolver import BaseResolver
from app.resolvers.encoding_resolvers import (
    BooleanResolver,
    LikertScaleResolver,
    MissingValueResolver,
    NumericTextResolver,
    PercentResolver,
)
from app.resolvers.structural_resolvers import (
    BlankColumnResolver,
    BlankRowResolver,
    BOMResolver,
    DuplicateColumnResolver,
    HeaderNormalizerResolver,
)
from app.resolvers.survey_resolvers import (
    CarryForwardResolver,
    DelimitedListResolver,
    MultiRowHeaderResolver,
    MultiSelectResolver,
)


def get_default_resolvers() -> List[BaseResolver]:
    """
    Return a fresh, ordered list of resolvers for each pipeline run.

    A new list is returned on every call — resolvers must remain stateless,
    but this prevents any accidental cross-run state if a future resolver
    ever stores temporary data.
    """
    return [
        # --- Structural ---
        BOMResolver(),
        BlankColumnResolver(),
        BlankRowResolver(),
        HeaderNormalizerResolver(),
        DuplicateColumnResolver(),
        # --- Encoding ---
        BooleanResolver(),
        LikertScaleResolver(),
        PercentResolver(),
        NumericTextResolver(),
        MissingValueResolver(),
        # --- Survey-specific ---
        MultiRowHeaderResolver(),
        MultiSelectResolver(),
        DelimitedListResolver(),
        CarryForwardResolver(),
    ]
