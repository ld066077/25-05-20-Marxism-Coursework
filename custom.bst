% 基于 unsrtnat.bst 修改
ENTRY
  { address
    author
    booktitle
    chapter
    edition
    editor
    howpublished
    institution
    journal
    key
    month
    note
    number
    organization
    pages
    publisher
    school
    series
    title
    type
    volume
    year
  }
  {}
  { label }

INTEGERS { output.state before.all mid.sentence after.sentence after.block }

FUNCTION {init.state.consts}
{ #0 'before.all :=
  #1 'mid.sentence :=
  #2 'after.sentence :=
  #3 'after.block :=
}

% ... (其他函数保持不变)

FUNCTION {article}
{ output.bibitem
  author.space
  title.field
  journal emphasize field.or.null
  volume.field
  number.field
  pages.field
  year.field
  note.field
  fin.entry
}

% ... (其他条目类型保持不变) 