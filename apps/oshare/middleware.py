'''
Created on 26 Feb 2010

@author: dalore
'''
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.utils import simplejson
from oshare.utils import json_encode


class JsonResponse(HttpResponse):
    """
    HttpResponse descendant, which return response with ``application/json`` mimetype.
    """
    def __init__(self, data):
        super(JsonResponse, self).__init__(content=json_encode(data), mimetype='application/json')

class DualFormatMiddleware(object):
    '''
    classdocs
    '''


    def process_response(self, request, response):
        '''
        Checks if the response is a dict, if so
        then it does one of two things. Checks if
        it is ajax, and if so returns it rendered as
        an ajax response. If not then checks for TEMPLATE
        in the dict and renders it.
        '''
        if not isinstance(response, dict):
            return response
        tmpl = response.pop('TEMPLATE')
        if request.is_ajax():
            return JsonResponse(response)
        return render_to_response(tmpl, response, context_instance=RequestContext(request))