import json
from app.config import AI_PROVIDER
from app.providers import ask
from app.workspace import read_text_files, apply_changes
from app.verifier import verify

def repair_project(project, request):
    all_errors=[]
    last_summary=""
    provider_used=""
    for attempt in range(2):
        context=read_text_files(project)
        prompt_request=request
        if all_errors:
            prompt_request += "\nFix the following verification errors from the previous attempt:\n" + "\n".join(all_errors)
        result, provider_used = ask(AI_PROVIDER, _build_prompt(prompt_request, context, all_errors))
        last_summary=result.get("summary","")
        changes=result.get("changes",[])
        applied=apply_changes(project, changes)
        all_errors=verify(project)
        if not all_errors:
            return {"ok":True,"summary":last_summary,"provider":provider_used,"files":applied,"errors":[],"attempts":attempt+1}
    return {"ok":False,"summary":last_summary,"provider":provider_used,"files":applied if 'applied' in locals() else [],"errors":all_errors,"attempts":2}

def _build_prompt(request, context, errors):
    return request + "\n\nPROJECT CONTEXT:\n" + context + "\n\nCURRENT ERRORS:\n" + ("\n".join(errors) if errors else "none")
