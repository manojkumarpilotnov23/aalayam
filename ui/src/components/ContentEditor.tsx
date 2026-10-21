import { useEditor, EditorContent } from '@tiptap/react'
import { useEffect } from 'react'
import StarterKit from '@tiptap/starter-kit'
import Link from '@tiptap/extension-link'

interface Props {
  value: string
  onChange: (html: string) => void
  placeholder?: string
}

export default function ContentEditor({ value, onChange, placeholder }: Props) {
  const editor = useEditor({
    extensions: [
      StarterKit,
      Link.configure({ openOnClick: false }),
    ],
    content: value,
    editorProps: {
      attributes: {
        'data-placeholder': placeholder ?? 'Enter content…',
      },
    },
    onUpdate({ editor }) {
      onChange(editor.getHTML())
    },
  })

  // Sync editor content when value changes externally (e.g. temple dropdown selection)
  useEffect(() => {
    if (!editor) return
    const current = editor.getHTML()
    if (current !== value) {
      editor.commands.setContent(value)
    }
  }, [value, editor])

  if (!editor) return null

  const btn = (active: boolean) =>
    `px-2 py-1 rounded text-sm border ${active ? 'bg-amber-600 text-white border-amber-600' : 'border-amber-300 text-amber-800 hover:bg-amber-100'}`

  return (
    <div className="border border-amber-300 rounded-lg overflow-hidden">
      <div className="flex flex-wrap gap-1 p-2 border-b border-amber-200 bg-amber-50">
        <button type="button" className={btn(editor.isActive('bold'))}
          onMouseDown={e => { e.preventDefault(); editor.chain().focus().toggleBold().run() }}>B</button>
        <button type="button" className={btn(editor.isActive('italic'))}
          onMouseDown={e => { e.preventDefault(); editor.chain().focus().toggleItalic().run() }}>I</button>
        <button type="button" className={btn(editor.isActive('heading', { level: 2 }))}
          onMouseDown={e => { e.preventDefault(); editor.chain().focus().toggleHeading({ level: 2 }).run() }}>H2</button>
        <button type="button" className={btn(editor.isActive('heading', { level: 3 }))}
          onMouseDown={e => { e.preventDefault(); editor.chain().focus().toggleHeading({ level: 3 }).run() }}>H3</button>
        <button type="button" className={btn(editor.isActive('bulletList'))}
          onMouseDown={e => { e.preventDefault(); editor.chain().focus().toggleBulletList().run() }}>• List</button>
        <button type="button" className={btn(false)}
          onMouseDown={e => { e.preventDefault(); editor.chain().focus().unsetAllMarks().clearNodes().run() }}>Clear</button>
      </div>
      <EditorContent editor={editor} className="bg-white" />
    </div>
  )
}
