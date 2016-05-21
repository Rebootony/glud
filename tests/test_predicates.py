from . base_glud_test import *
import clang.cindex
from clang.cindex import *
from toolz import count, filter

class PredicateTests(BaseGludTest):

    def test_find_classes(self):
        s = '''
        class Foo;
        class Foo {};
        '''
        root = self.parse(s)
        it = glud.walk(is_class, root)
        self.assertEqual(2, count(it))

    def test_can_ignore_forward_declaration(self):
        s = '''
        class Foo;
        class Foo {};
        '''
        root = self.parse(s)
        classes = glud.walk(is_class_definition, root)
        self.assertEqual(1, count(classes))

    def test_template_class(self):
        s = '''
        template<class T> class Foo {};
        '''
        root = self.parse(s)
        classes = glud.walk(is_class, root)
        self.assertEqual(0, count(classes))

    def test_find_nested_classes(self):
        s = '''
        class Foo {
            class Bar {};
        };
        '''
        root = self.parse(s)
        classes = glud.walk(is_class_definition, root)
        classes = list(classes)
        self.assertEqual(2, count(classes))

    def test_named_match_pinned_at_end(self):
        s = '''
        void f();
        void f1();
        void f10();
        '''
        root = self.parse(s)
        funcs = glud.walk(is_function, root)
        funcs = filter(match_name('f'), funcs)
        funcs = list(funcs)
        self.assertEqual(1, count(funcs))
        self.assertEqual(bool, type(match_name('f', funcs[0])))


    def test_find_class_with_named_method(self):
        s = '''
        class Foo {
        public:
            void f();
            void f(int);
        };

        class Bar {
        public:
            void f();
        };

        class Baz {
        public:
            void g();
        };
        '''
        root = self.parse(s)
        f = all_fn([
            is_class_definition,
            any_child(all_fn([
                is_public,
                is_method,
                match_name('f')
            ]))
        ])
        classes = glud.walk(f, root)
        self.assertEqual(2, count(classes))

    def test_has_access_curried(self):
        c = self.parse('class foo{};')
        # curry function
        f = has_access(clang.cindex.AccessSpecifier.PROTECTED)
        walk(f, c)

    def test_enums_types(self):
        s = '''
        enum EmptyEnum {
        };

        enum Bar {
            XXX,
            YYY
        };

        namespace ns {
            enum Baz {
                AAA,
                BBB
            };
        }
        '''
        root = self.parse(s)
        enums = glud.walk(is_enum, root)
        es  = list(enums)
        self.assertEqual('EmptyEnum', es[0].type.spelling)
        self.assertEqual('Bar', es[1].type.spelling)
        self.assertEqual('ns::Baz', es[2].type.spelling)

    def test_methods(self):
        s = '''
        class Foo
        {
        public:
            void f();
        };
        '''
        root = self.parse(s)

        f = all_fn([
            is_in_file(set(['tmp.cpp'])),
            is_method,
            match_name('f'),
        ])
        ms = list(glud.walk(f, root))
        self.assertTrue(is_primitive(ms[0].result_type))

    def test_access_specifiers(self):
        s = '''
        class foo {
        public:
            void f1();
        protected:
            void g1();
            void g2();
        private: 
            void h1();
            void h2();
            void h3();
        };
        '''
        root = self.parse(s)
        def cnt_match(f, root):
            return count(glud.walk(all_fn([is_method, f]), root))
        self.assertEqual(1, cnt_match(is_public, root))
        self.assertEqual(2, cnt_match(is_protected, root))
        self.assertEqual(3, cnt_match(is_private, root))

    def test_haslocation(self):
        s = 'void f();'
        root = self.parse(s, options=TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD)
        ms = glud.walk(has_location, root)
        list(ms)

    def test_function(self):
        s = '''
        void f();
        '''
        root = self.parse(s)
        fs = glud.walk(is_function, root)
        self.assertEqual(1, count(fs))

    def test_typematch_name(self):
        s = '''
        class foo;
        namespace bar {
            class foo;
        }
        '''
        root = self.parse(s)
        fs = glud.walk(match_typename('bar::foo'), root)
        self.assertEqual(1, count(fs))

    def test_any_predecessor(self):
        s = '''
        namespace foo {
            namespace bar {
                class baz {} ;
            }
            class biz {} ;
        }
        '''
        root = self.parse(s)
        f = any_predecessor(lambda c : c.semantic_parent, match_name('bar'))
        classes = glud.walk(all_fn([is_class, f]), root)
        self.assertEqual(1, count(classes))

    def test_all_children(self):
        s = '''
        class foo {
        public:
            int x;
            int y;
        };
        class bar {
        public: 
            int x;
            int y;
        private: 
            int z;
        };
        '''
        root = self.parse(s)
        f = all_fn([
            is_class,
            all_children(is_public)
        ])
        classes = glud.walk(f, root)
        self.assertEqual(1, count(classes))

    def test_any_fn(self):
        s = '''
        class biz {
            void f();
            int g;
            enum baz {};
            class moo {};
        };
        '''
        root = self.parse(s)
        it = glud.walk(any_fn([is_method, is_enum]), root)
        self.assertEqual(2, count(it))


    def test_all_pred(self):
        s = '''
        namespace foo {
            namespace bar {
                class fizz;
            }
            class buzz;
            class mazz;
        }
        '''
        f = all_predecessors(
            lambda s:s.semantic_parent,
            any_fn([
                is_translation_unit,
                all_fn([
                    is_namespace,
                    match_name('foo')
                ])
            ])
        )
        root = self.parse(s)
        it = glud.walk(f, root)
        self.assertEqual(2, count(it))


