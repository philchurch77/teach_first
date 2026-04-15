from django.shortcuts import render, redirect
from .flow_data import FLOW

# Create your views here.
def flow_view(request):

    node_id = request.GET.get("node") or request.session.get("node_id") or "start"
    node = FLOW.get(node_id, FLOW["start"])

    if request.method == "POST":
        next_id = request.POST.get("next")
        if next_id in FLOW:
            request.session["node_id"] = next_id
            return redirect("flow")
        request.session["node_id"] = "start"
        return redirect("flow")
    
    request.session["node_id"] = node_id
    return render(request, "flow/flow.html", {"node": node})