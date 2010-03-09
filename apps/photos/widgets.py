'''
Created on Mar 2, 2010

@author: neild
'''

from itertools import chain
import math

from django.forms.widgets import CheckboxInput, SelectMultiple
from django.utils.encoding import force_unicode
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe


class TableCheckboxSelectMultiple(SelectMultiple):
    def __init__(self, attrs=None, choices=(), thumb_urls=(), cols_count=5):
        super(TableCheckboxSelectMultiple, self).__init__(attrs, choices)
        self.thumb_urls = thumb_urls
        self.cols_count = cols_count
    
    # TODO: move html part into a template and render that    
    def render(self, name, value, attrs=None, choices=()):
        if value is None: value = []
        has_id = attrs and 'id' in attrs
        final_attrs = self.build_attrs(attrs, name=name)
        output = [u'<table>']
        # Normalize to strings
        str_values = set([force_unicode(v) for v in value])
        # build table
        all_choices = list(chain(self.choices, choices))
        rows_count = math.ceil(len(all_choices) / float(self.cols_count)) 
        for row in range(0, rows_count):
            start = row*self.cols_count
            output.append(u'<tr>')
            for i in range(start, start+self.cols_count):
                if i >= len(all_choices):
                    output.append(u'<td>&nbsp;</td>')
                else:
                    (option_value, option_label) = all_choices[i]
                    output.append(u'<td>')
                    # If an ID attribute was given, add a numeric index as a suffix,
                    # so that the checkboxes don't all have the same ID attribute.
                    if has_id:
                        final_attrs = dict(final_attrs, id='%s_%s' % (attrs['id'], i))
                        label_for = u' for="%s"' % final_attrs['id']
                    else:
                        label_for = ''
        
                    cb = CheckboxInput(final_attrs, check_test=lambda value: value in str_values)
                    option_value = force_unicode(option_value)
                    rendered_cb = cb.render(name, option_value)
                    option_label = conditional_escape(force_unicode(option_label))
                    output.append(u'<div><img src="%s"/></div>' % self.thumb_urls[i]) 
                    output.append(u'<div><label%s>%s %s</label></div>' % (label_for, rendered_cb, option_label))
                    output.append(u'</td>')
            output.append(u'</tr>')
       
        output.append(u'</table>')
        
        return mark_safe(u'\n'.join(output))

    def id_for_label(self, id_):
        # See the comment for RadioSelect.id_for_label()
        if id_:
            id_ += '_0'
        return id_
    id_for_label = classmethod(id_for_label)
