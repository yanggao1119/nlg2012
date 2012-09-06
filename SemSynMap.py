'''
Created on Aug 16, 2012

@author: yaqiny
'''
import on
from Head import head
#from nltk import ParentedTree
from on.corpora import tree
#import AMR 
import re

from collections import defaultdict
import pickle

class semSynMap(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
    def getAOntonotes(self):
        '''
        See on/__init__.py for usages of ontonotes object
        '''
        '''
        Create a config object
        '''
        cfg = on.common.util.load_options(positional_args=False)
        '''
        Create an ontonotes object by passing in a config object
        '''
        a_ontonotes = on.ontonotes(cfg)
        
        return a_ontonotes
    
#    def sortBySynOrder(self,a_prop_analogue,sort_by_arg_id):
#        '''
#        a list of analogue
#        nw/wsj/00/wsj_0002@all@wsj@nw@en@on 0 16 gold name-v name.01 ----- 16:0-rel 0:2*17:0*18:0-ARG1 18:2-ARG2 17:0*17:0-LINK-PCR
#        '''
#        sort_by_syn_order = []
#        order_dict = defaultdict()
#        for a_role in a_prop_analogue.enc_prop.split("-----")[1].strip().split():
#            
#            node_pos_list = map(lambda x:x.split(":")[0], a_role.split("-")[0].split("*"))
#            node_pos_list = sorted(node_pos_list, key=lambda x:int(x))
#            
#            node_role = a_role.split("-")[1]
#            
#            for a_ana in sort_by_arg_id:
#                cur_ana_role = "-".join(a_ana.enc_self.split("-")[1:])
#                if cur_ana_role == node_role:
#                    order_dict[int(node_pos_list[0])]=a_ana
#        
#        for i in sorted(order_dict.iterkeys()):
#            sort_by_syn_order.append(order_dict[i])
#            
#        return sort_by_syn_order

    def sortBySynOrder(self,a_prop_analogue,sort_by_arg_id):
        '''
        a list of analogue
        nw/wsj/00/wsj_0002@all@wsj@nw@en@on 0 16 gold name-v name.01 ----- 16:0-rel 0:2*17:0*18:0-ARG1 18:2-ARG2 17:0*17:0-LINK-PCR
        '''
        sort_by_syn_order = []
        order_dict = defaultdict()
        for a_role in a_prop_analogue.enc_prop.split("-----")[1].strip().split():
            
            node_pos_list = map(lambda x:x.split(":")[0], a_role.split("-")[0].split(",")[0].split(";")[0].split("*"))
            node_pos_list = sorted(node_pos_list, key=lambda x:int(x))
            
            node_role = a_role.split("-")[1]
            
            for a_ana in sort_by_arg_id:
                cur_ana_role = "-".join(a_ana.enc_self.split("-")[1:])
                if cur_ana_role == node_role:
                    order_dict[int(node_pos_list[0])]=a_ana
        
        for i in sorted(order_dict.iterkeys()):
            sort_by_syn_order.append((order_dict[i],i))
            
        return sort_by_syn_order

        
        
    def getPredicateRule(self,a_tree_document,sort_by_arg_id,a_prop_analogue):
        '''
        q.(/ die-01 :ARG1 x0) -> S(qnp.x0 VB(die))
        qs.(:rest=[/ die-01] x0 :ARG1 x1) -> S(qnp.x1 VP(qvp.x0))
        '''
        output_rule = ""
        arg_var_dict = defaultdict()        
        pred_lemma_sense_num=""
        if len(sort_by_arg_id) == 1:
            print "the adj verb has no argument????"
            return None

#        sort_by_arg_id = sorted(role_rel_list, key=lambda x:"-".join(x.enc_self.split("-")[1:]))
        sort_by_syn_order = self.sortBySynOrder(a_prop_analogue, sort_by_arg_id)
        sort_by_syn_order = map(lambda x:x[0],sort_by_syn_order)
#        sort_by_syn_order = sorted(sort_by_arg_id, key=lambda x:int(x.enc_self.split(":")[0]))

        '''
        predicate is at the end of the list -- sort_by_arg_id[-1]
        '''        
        arg_var_dict[sort_by_arg_id[-1]]="x0"     
        output_rule = "qs.(:rest=[/ "+"PREDICATE"+"] " +arg_var_dict[sort_by_arg_id[-1]]
        
        
        for i, a_ana in enumerate(sort_by_arg_id):
            if isinstance(a_ana,on.corpora.proposition.argument_analogue):
                cur_arg_role = "-".join(a_ana.enc_self.split("-")[1:])
                arg_var_dict[a_ana]="x"+str(i+1)
                output_rule += " :"+cur_arg_role+" "+arg_var_dict[a_ana]
#            if isinstance(a_ana,on.corpora.proposition.predicate_analogue):
                
        output_rule += ")) -> S("
        
        for i, a_ana in enumerate(sort_by_syn_order):
            if isinstance(a_ana,on.corpora.proposition.predicate_analogue):
                pred_lemma_sense_num, pred_type, pred_token_index, sentence_index, document_id = a_ana.id.split("@")[:5]
                pred_lemma_sense_num = re.sub("\.","-",pred_lemma_sense_num)
                leaves = a_tree_document[a_ana.sentence_index].leaves()
                current_pred = leaves[int(pred_token_index)]
                output_rule += "VP("
                if self.isPassive(current_pred):
                    output_rule += "qvp_pass."+arg_var_dict[a_ana]+" " 
                else:
                    output_rule += "qvp."+arg_var_dict[a_ana]+" " 
                    
            if isinstance(a_ana,on.corpora.proposition.argument_analogue):
                arg_role = "-".join(a_ana.enc_self.split("-")[1:])
                core_subtree, r_subtrees, c_subtrees = a_ana.get_subtree_tuple()
                qstate = self.getState(core_subtree, r_subtrees, c_subtrees).lower()
                pp_word = ""
                if qstate == "":
                    raw_input("core_subtree is null")
                
                if qstate == "pp":
                    pp_word = core_subtree.leaves()[0].word.lower()
                    pp_word = "IN("+pp_word+") "
                    qstate = "np"
                output_rule += pp_word+"q"+qstate+"."+arg_var_dict[a_ana]+" "
                
        if pred_lemma_sense_num=="":
            return None
        output_rule = re.sub("PREDICATE",pred_lemma_sense_num,output_rule)
        output_rule = output_rule.strip()
        output_rule += "))"
        return output_rule
    
    def getModRule(self,a_tree_document,sort_by_arg_id,inverse_arg_index,vtag,a_prop_analogue):
        '''
        qnp.(/ x0 :ARG0-of (/ publish-01)) -> NP(VBG(published) qnp.x0)
        '''
        output_rule = ""
        arg_var_dict = defaultdict()        
#        if len(args_list) > 1:
#            print args_list,role_rel_list,pred_lemma_sense_num
#            print "the adj verb has two arguments????"
#            return False
        if len(sort_by_arg_id) == 1:
            print role_rel_list
            print "the adj verb has no argument????"
            return None

#        sort_by_arg_id = sorted(role_rel_list, key=lambda x:"-".join(x.enc_self.split("-")[1:]))
        sort_by_syn_order = self.sortBySynOrder(a_prop_analogue, sort_by_arg_id)
        sort_by_syn_order = map(lambda x:x[0],sort_by_syn_order)
#        sort_by_syn_order = sorted(sort_by_arg_id, key=lambda x:int(x.enc_self.split(":")[0]))
#        print "sort by arg", map(lambda x:x.enc_self,sort_by_arg_id)
#        print "sort by syn order", map(lambda x:x.enc_self,sort_by_syn_order)
        pred_lemma_sense_num=""
        inverse_arg_ana = sort_by_arg_id[inverse_arg_index]
        inverse_arg_role = "-".join(inverse_arg_ana.enc_self.split("-")[1:])
        
        arg_var_dict[inverse_arg_ana]="x0"        
        output_rule = "qnp.(/ "+arg_var_dict[inverse_arg_ana]+" :"+inverse_arg_role+"-of"+"(/ "+"PREDICATE"
        
        for i, a_ana in enumerate(sort_by_arg_id):
            if isinstance(a_ana,on.corpora.proposition.argument_analogue):
                cur_arg_role = "-".join(a_ana.enc_self.split("-")[1:])
                if i < inverse_arg_index:
                    arg_var_dict[a_ana]="x"+str(i+1)
                elif i > inverse_arg_index:
                    arg_var_dict[a_ana]="x"+str(i)
                if i != inverse_arg_index:
                    output_rule += " :"+cur_arg_role+" "+arg_var_dict[a_ana]
#            if isinstance(a_ana,on.corpora.proposition.predicate_analogue):
                
        output_rule += ")) -> NP("
        
        
        for i, a_ana in enumerate(sort_by_syn_order):
            if isinstance(a_ana,on.corpora.proposition.predicate_analogue):
                pred_lemma_sense_num, pred_type, pred_token_index, sentence_index, document_id = a_ana.id.split("@")[:5]
                pred_lemma_sense_num = re.sub("\.","-",pred_lemma_sense_num)
                leaves = a_tree_document[a_ana.sentence_index].leaves()
                current_pred = leaves[int(pred_token_index)]
                output_rule += vtag+"("+current_pred.word.lower()+") " 
            if isinstance(a_ana,on.corpora.proposition.argument_analogue):
                arg_role = "-".join(a_ana.enc_self.split("-")[1:])
                core_subtree, r_subtrees, c_subtrees = a_ana.get_subtree_tuple()
                qstate = self.getState(core_subtree, r_subtrees, c_subtrees).lower()
                pp_word = ""
                if qstate == "":
                    raw_input("core_subtree is null")
                
                if qstate == "pp":
                    pp_word = core_subtree.leaves()[0].word.lower()
                    pp_word = "IN("+pp_word+") "
                    qstate = "np"
                output_rule += pp_word+"q"+qstate+"."+arg_var_dict[a_ana]+" "
                
        if pred_lemma_sense_num=="":
            return None

        output_rule = re.sub("PREDICATE",pred_lemma_sense_num,output_rule)
        output_rule = output_rule.strip()
        output_rule += ")"
        return output_rule
    
    def getState(self,core_subtree, r_subtrees, c_subtrees):
        state = "np"
        try:
            if core_subtree != [] or core_subtree != None:
                state =  core_subtree.tag
                if re.match("V|v",state):
                    state = "vp"
                elif re.match("pp",state.lower()):
                    state = "pp"
                elif re.match("s",state.lower()):
                    state = "s"
                else:
                    state = "np"
        except:
            return state
        return state
    
    def isPredicate(self,node):
        prev_node = node
        node = node.parent
        while not node.is_root() and re.match("V|S",node.tag):
            prev_node = node
            node = node.parent
        if not node.is_root():
            return False
        return True
    
    def isInfinitive(self,node):
        if not re.match("vb$",node.tag.lower()):
            return False
        while not node.is_root() and not re.match("VP",node.tag):
            node = node.parent
        if re.match("vp",node.tag.lower()):  
            ls = self.getLeftSibling(node)
            while ls != None:
                if len(ls.leaves()) == 1 and ls.leaves()[0].tag == "TO":
                    return True
                
                ls = self.getLeftSibling(ls)
        return False
                 
    def isPassive(self,node):
        '''
        not a good pattern.....
        '''
        if not re.match("vbn",node.tag.lower()):
            return False
        cop_list = "be been is am are was were".split()
        ax_list = "have has had".split()
        pred_node = node
        pred_token_index = pred_node.get_token_index()
        parent_node = node
        node = node.parent
    
        while not node.is_root() and re.match("V",node.tag):
            parent_node = node
            node = node.parent
        if re.match("v",parent_node.tag.lower()):
            leaves_list = parent_node.leaves()
            inside_index = 0
            first_node = leaves_list[inside_index]
            first_node_token_index = first_node.get_token_index()
            while first_node_token_index < pred_token_index:
                if first_node.word.lower() in cop_list and re.match("v",first_node.tag.lower()):
                    return True
                inside_index += 1
                first_node = leaves_list[inside_index]
                first_node_token_index = first_node.get_token_index()
        return False
        
#        if re.match("V",prev_node.tag):
#            leaves_list = prev_node.leaves()
#            first_node = leaves_list[0]
#            if first_node == pred_node:
#                return False
#            if first_node.word in cop_list and re.match("v",first_node.tag.lower()):
#                return True
#            try:
#                seconde_node = leaves_list[1]
#                if first_node.word in ax_list and seconde_node.word.lower() in ["been"]:
#                    return True
#                if first_node.word in "will would could should must".split() and seconde_node.word.lower() in ["be"]:
#                    return True            
#            except:
#                return False
#        return False
                        
            
    
    def isPreMod(self,node,sort_by_arg_id,vtag):
        '''
        noun-modifiers, participles 
        '''
        if node.tag == vtag:
            prev_node = node
            node = node.parent
            while not node.is_root() and re.match("N|ADJP",node.tag):# and not re.match("S",node.tag) and not re.match("VP",node.tag) and not re.match("PP",node.tag):
                if re.match("N",node.tag):
                    right_sibling = self.getRightSibling(prev_node)
                    if right_sibling != None:
                        for i,a_ana in enumerate(sort_by_arg_id):
                            if isinstance(a_ana,on.corpora.proposition.argument_analogue):
                                arg_role = "-".join(a_ana.enc_self.split("-")[1:])
                                core_subtree, r_subtrees, c_subtrees = a_ana.get_subtree_tuple()
                                if core_subtree == right_sibling and re.match("N",right_sibling.tag):
                                    '''
                                        (NP (DT the)
                                            (VBN renovated)
                                            (NML (NNP Indiana)
                                                 (NNP Roof))
                                            (NN ballroom)))))
                                    8:0,9:0,10:0-ARG1
                                    ((NNP Indiana), [], [(NNP Roof), (NN ballroom)])                    
                                    '''
                                    return "inver_"+str(i)
                    return False
                prev_node = node
                node = node.parent
        return False
    
    def getRightSibling(self,node):
        if node.child_index < len(node.parent.children) - 1:
            return node.parent.children[node.child_index+1]
        return None
    
    def getLeftSibling(self,node):
        if node.child_index > 0:
            return node.parent.children[node.child_index-1]        
        return None
    
    def getCoreArgs(self,arguments):
        args_list = []
        for a_arg_analogue in  arguments:
            a_arg_analogue_info = a_arg_analogue.enc_self
            arg_treepos = a_arg_analogue_info.split("-")[0]
            arg_role = "-".join(a_arg_analogue_info.split("-")[1:])
            if not re.match("ARG[0-9]+",arg_role):
                '''
                only keep the core roles
                '''
                continue
            args_list.append(arg_role)
        return args_list

    def getArgDict(self,prop_analogue):
        '''
        key is the position
        value is the argument
        '''
        "nw/wsj/00/wsj_0019@all@wsj@nw@en@on 5 7 gold name-v name.01 ----- 7:0-rel 0:2*8:0*9:0-ARG1 9:2-ARG2 8:0*8:0-LINK-PCR"
        roles_dict = defaultdict()
        roles = map(lambda x:x.strip(),prop_analogue.enc_prop.split("-----")[1].split())
        pred_ana = prop_analogue.predicate
        args_ana = prop_analogue.argument_analogues
        role_pos_dict = defaultdict()
        for a_role in roles:
            positions = a_role.split("-")[0]
            arg_role = "-".join(a_role.split("-")[1:])
            arg_pos =positions.split(",")[0]
            arg_pos =positions.split(";")[0]
            roles_dict[arg_role] = arg_pos
        role_pos_dict[pred_ana] = roles_dict["rel"]
        for a_arg_ana in args_ana:
            arg_role = "-".join(a_arg_ana.enc_self.split("-")[1:])
            role_pos_dict[a_arg_ana] = roles_dict[arg_role]
            
            
#            if not re.match("ARG[0-9]+",arg_role):
#                continue
#            concatenate_pos = []
#            
#            if len(positions.split(",")) == 2:
#                concatenate_pos = positions.split(",")[-1]
#                arg_role += "|"+concatenate_pos
#            for a_arg_pos in arg_pos.split("*"):
#                if a_arg_pos not in roles_dict:
#                    roles_dict[a_arg_pos] = [arg_role]
#                else:
#                    roles_dict[a_arg_pos].append(arg_role)
#                    
        return role_pos_dict

    def getVpAntecedent(self,pred_ana,a_tree_document):
        leaves = a_tree_document[pred_ana.sentence_index].leaves()
        pred_token_index = pred_ana.token_index
        current_pred = leaves[int(pred_token_index)]
        prev_node = current_pred
        while not current_pred.is_root() and re.match("V",current_pred.tag):
            prev_node = current_pred
            current_pred = current_pred.parent
        return prev_node
        
        
    def isControl(self,x_prop_ana, y_prop_ana,a_tree_document,head_rules):
        he = head()
        x_pred_ana = x_prop_ana.predicate
        y_pred_ana = y_prop_ana.predicate
        x_pred_lemma_sense_num, x_pred_type, x_pred_token_index, x_sentence_index, x_document_id = x_pred_ana.id.split("@")[:5]
        y_pred_lemma_sense_num, y_pred_type, y_pred_token_index, y_sentence_index, y_document_id = y_pred_ana.id.split("@")[:5]
        x_pred_token_index = int(x_pred_token_index)
        y_pred_token_index = int(y_pred_token_index)
        x_sentence_index = int(x_sentence_index)
        y_sentence_index = int(y_sentence_index)
        x_pred_node = a_tree_document[x_sentence_index].leaves()[x_pred_token_index]
        y_pred_node = a_tree_document[y_sentence_index].leaves()[y_pred_token_index]
        
        if x_pred_token_index < y_pred_token_index:
            vp_node = self.getVpAntecedent(x_pred_ana, a_tree_document)
            
            if not he.isHeadLeaf(head_rules,vp_node, x_pred_node):
                return False
            first_child = vp_node.children[0]
            x_right_sibling = self.getRightSibling(first_child)
            while x_right_sibling != None and not re.match("S$",x_right_sibling.tag.split("-")[0]):
                x_right_sibling = self.getRightSibling(x_right_sibling)
            if x_right_sibling != None and re.match("S$", x_right_sibling.tag.split("-")[0]) and he.isHeadLeaf(head_rules,x_right_sibling,y_pred_node):
                
                return True
      
        return False
    
    def inAnaDict(self, x_ana, ana_dict,x_y_arg_pos_dict):
        x_pos = x_y_arg_pos_dict[x_ana]
        
        for a_ana in ana_dict:
            if isinstance(a_ana,on.corpora.proposition.argument_analogue):
                a_pos = x_y_arg_pos_dict[a_ana]
                
                if x_pos == a_pos:
                    return a_ana
        
        return False
                
    def deleteDuplicate(self, xy_sort_by_syn_order,x_y_arg_pos_dict):
        syn_dict = {}
        for a_ana, index in xy_sort_by_syn_order:
            if isinstance(a_ana,on.corpora.proposition.argument_analogue):
                if x_y_arg_pos_dict[a_ana] not in syn_dict.keys():
                    syn_dict[x_y_arg_pos_dict[a_ana]] = (a_ana,index)
            else:
                syn_dict[len(syn_dict)+1] = (a_ana,index)
        return syn_dict.values()
    
    def getMaxIndex(self,arg_var_dict):
        mi = -1
        for v in arg_var_dict.values():
            ci = int(v[1:])
            if ci > mi:
                mi = ci
        return mi
    
    def getControlRule(self,x_prop_ana, y_prop_ana,x_sort_by_arg_id,y_sort_by_arg_id,a_tree_document):
        '''qs.(:rest=[/ want-01] x0 :ARG0 x1 :ARG2(:rest=[/ go-01] x2 :ARG0 x1)) -> S(qnp.x1 VP(qvp.x0 TO(to) qvp.x2))'''
        x_pred_ana = x_prop_ana.predicate
        y_pred_ana = y_prop_ana.predicate
        x_pred_lemma_sense_num, x_pred_type, x_pred_token_index, x_sentence_index, x_document_id = x_pred_ana.id.split("@")[:5]
        y_pred_lemma_sense_num, y_pred_type, y_pred_token_index, y_sentence_index, y_document_id = y_pred_ana.id.split("@")[:5]
        x_pred_token_index = int(x_pred_token_index)
        y_pred_token_index = int(y_pred_token_index)
        x_sentence_index = int(x_sentence_index)
        y_sentence_index = int(y_sentence_index)
        x_pred_node = a_tree_document[x_sentence_index].leaves()[x_pred_token_index]
        y_pred_node = a_tree_document[y_sentence_index].leaves()[y_pred_token_index]
        x_arg_pos_dict = self.getArgDict(x_prop_ana)
        y_arg_pos_dict = self.getArgDict(y_prop_ana)
        x_y_arg_pos_dict = dict(x_arg_pos_dict.items() + y_arg_pos_dict.items())

        
        output_rule = ""
        arg_var_dict = defaultdict()        
        pred_lemma_sense_num=""
        if len(x_sort_by_arg_id) == 1 or len(y_sort_by_arg_id) == 1:
            print "the adj verb has no argument????"
            return None

        x_sort_by_syn_order = self.sortBySynOrder(x_prop_ana, x_sort_by_arg_id)
        y_sort_by_syn_order = self.sortBySynOrder(y_prop_ana, y_sort_by_arg_id)

        xy_sort_by_syn_order = x_sort_by_syn_order
        xy_sort_by_syn_order.extend(y_sort_by_syn_order)
        xy_sort_by_syn_order =  self.deleteDuplicate(xy_sort_by_syn_order,x_y_arg_pos_dict)
        xy_sort_by_syn_order = sorted(xy_sort_by_syn_order, key=lambda x:int(x[1]))
        xy_sort_by_syn_order = map(lambda x:x[0],xy_sort_by_syn_order)
        
        
        '''
        predicate is at the end of the list -- sort_by_arg_id[-1]
        '''        
        arg_var_dict[x_sort_by_arg_id[-1]]="x0"     
        x_pred_lemma_sense_num = re.sub("\.","-",x_pred_lemma_sense_num)
        y_pred_lemma_sense_num = re.sub("\.","-",y_pred_lemma_sense_num)
        output_rule = "qs.(:rest=[/ "+x_pred_lemma_sense_num+"] " +arg_var_dict[x_sort_by_arg_id[-1]]
        
        '''qs.(:rest=[/ want-01] x0 :ARG0 x1 :ARG2(:rest=[/ go-01] x2 :ARG0 x1)) -> S(qnp.x1 VP(qvp.x0 TO(to) qvp.x2))'''
        '''a_args_dict,b_args_dic'''
        x_contain_y = False
        for i, a_ana in enumerate(x_sort_by_arg_id):
            if isinstance(a_ana,on.corpora.proposition.argument_analogue):
                cur_arg_role = "-".join(a_ana.enc_self.split("-")[1:])
                if self.includeNode(a_ana, y_pred_ana):
                    x_contain_y = True
                    arg_var_dict[y_pred_ana]="x"+str(self.getMaxIndex(arg_var_dict)+1)    
                    output_rule += " :"+cur_arg_role+"(:rest=[/ "+y_pred_lemma_sense_num+"] "+arg_var_dict[y_pred_ana]
                    for j, b_ana in enumerate(y_sort_by_arg_id):
                        if isinstance(b_ana,on.corpora.proposition.argument_analogue):
                            b_cur_arg_role = "-".join(b_ana.enc_self.split("-")[1:])
                            reent = self.inAnaDict(b_ana, arg_var_dict,x_y_arg_pos_dict)
                            if reent:
                                arg_var_dict[b_ana]=arg_var_dict[reent]
                            else:
                                arg_var_dict[b_ana]="x"+str(self.getMaxIndex(arg_var_dict)+1)   
                                 
                            output_rule += " :"+b_cur_arg_role+" "+arg_var_dict[b_ana]            
                    output_rule += ")"
                else:
                    reent = self.inAnaDict(a_ana, arg_var_dict,x_y_arg_pos_dict)
                    if reent:
                        arg_var_dict[a_ana]=arg_var_dict[reent]
                        
                    else:
                        arg_var_dict[a_ana]="x"+str(self.getMaxIndex(arg_var_dict)+1)   
                                             
                    output_rule += " :"+cur_arg_role+" "+arg_var_dict[a_ana]
        output_rule += ") -> S("
        
        if not x_contain_y:
            return None
        for i, a_ana in enumerate(xy_sort_by_syn_order):
            if a_ana not in arg_var_dict:
                continue
            if isinstance(a_ana,on.corpora.proposition.predicate_analogue):
                pred_lemma_sense_num, pred_type, pred_token_index, sentence_index, document_id = a_ana.id.split("@")[:5]
                pred_lemma_sense_num = re.sub("\.","-",pred_lemma_sense_num)
                leaves = a_tree_document[a_ana.sentence_index].leaves()
                current_pred = leaves[int(pred_token_index)]
                if self.isInfinitive(current_pred):
                    output_rule += "SINF(TO(to) "
                else:
                    output_rule += "VP("
                    
                if self.isPassive(current_pred):
                    output_rule += "qvp_pass."+arg_var_dict[a_ana]+" " 
                else:
                    output_rule += "qvp."+arg_var_dict[a_ana]+" " 
                    
            if isinstance(a_ana,on.corpora.proposition.argument_analogue):
                arg_role = "-".join(a_ana.enc_self.split("-")[1:])
                core_subtree, r_subtrees, c_subtrees = a_ana.get_subtree_tuple()
                qstate = self.getState(core_subtree, r_subtrees, c_subtrees).lower()
                pp_word = ""
                if qstate == "":
                    raw_input("core_subtree is null")
                if qstate == "pp":
                    pp_word = core_subtree.leaves()[0].word.lower()
                    pp_word = "IN("+pp_word+") "
                    qstate = "np"
                output_rule += pp_word+"q"+qstate+"."+arg_var_dict[a_ana]+" "
                
        if pred_lemma_sense_num=="":
            return None
        output_rule = output_rule.strip()
        output_rule += "))"
#        print output_rule
#        raw_input("control rule")
        return  output_rule

    

    def includeNode(self,x_arg_ana,y_pred_ana):
        '''
        if a predicate is the core argument of another one
        '''
        core_subtree, r_subtrees, c_subtrees = x_arg_ana.get_subtree_tuple()
        
        if core_subtree != None:
            core_subtree_leaves = core_subtree.leaves()
            y_pred_lemma_sense_num, y_pred_type, y_pred_token_index, y_sentence_index, y_document_id = y_pred_ana.id.split("@")[:5]
            x_start_token_index = int(core_subtree_leaves[0].get_token_index())
            x_end_token_index = int(core_subtree_leaves[-1].get_token_index())
            y_pred_token_index = int(y_pred_token_index)
#            print x_arg_ana.enc_self
#            print x_start_token_index,x_end_token_index, y_pred_token_index
            if y_pred_token_index >= x_start_token_index and y_pred_token_index <= x_end_token_index:
                return True
        return False
        
        
        
    def traverseTrees(self,output_dir,a_ontonotes,dev_test,head_rules):
        '''
        given an ontonotes object and iterate over the subcorpora it contains (usually only one subcorpus)
        '''
        '''
        a_subcorpus is a dictionary, containing a treebank for all fileids, a document and generally contains other banks.
        '''        
        vbn_premod_dict = {}
        vbg_premod_dict = {}
        predicate_dict = {}
        control_rule_dict = {}
        dev_test_id_dict =defaultdict()
        #output="/nfs/guest/yaqiny/Dropbox/Code/generation/rules/prop-anotation/propbank"
#        output="/home/nlg-01/yy_140/generation/Code/generation/rules/prop-anotation/propbank"
        output = output_dir
        
        dev_test_ids = open(dev_test,"r")
        for line in dev_test_ids:
            line = line.strip()
            dev_test_id_dict[line] = 0
            
        for a_subcorpus in a_ontonotes:
            a_tree_bank = a_subcorpus['parse']
            '''
            The treebank class represents a collection of :class:`tree_document` classes
            '''
            a_prop_bank = a_subcorpus['prop']
            prefix =  a_tree_bank.tree_ids[0].split("/")[2]
            gen = a_tree_bank.tree_ids[0].split("/")[0].split("@")[-1]
            ref_predicate_output_file = open(output+".ref.predicate."+gen+"."+prefix+".txt", "w")
            ref_control_output_file = open(output+".ref.control."+gen+"."+prefix+".txt", "w")
            for a_prop_document in a_prop_bank:
                a_tree_document = a_prop_document.tree_document
                doc_id =""
                sent_id = ""
                prev_doc_id = ""
                prev_sent_id = ""
                control_prev_doc_id = ""
                control_prev_sent_id = ""
                
                for a_index, a_prop in enumerate(a_prop_document):
                    doc_id, sent_id = a_prop.enc_prop.split()[0:2]
                    doc_genre=doc_id.split("/")[0]
                    doc_fileid=doc_id.split("@")[0].split("/")[-1]
                    file_id=doc_genre+"_"+doc_fileid+"_"+sent_id
                    
                    if file_id in dev_test_id_dict:
                        print "in dev"
                        continue
                                     
                    a_predicate_analogue = a_prop.predicate
                    pred_lemma_sense_num, pred_type, pred_token_index, sentence_index, document_id = a_predicate_analogue.id.split("@")[:5]
                    all_arguments = a_prop.argument_analogues
                    role_rel_list = []
                    
#                    sent_str = a_tree_document[a_predicate_analogue.sentence_index].to_string()
                    sent_str = " ".join(map(lambda x:x.word,a_tree_document[int(a_predicate_analogue.sentence_index)].leaves()))

                    leaves = a_tree_document[a_predicate_analogue.sentence_index].leaves()
                    pred_token_index = a_predicate_analogue.token_index
                    current_pred = leaves[int(pred_token_index)]
                    role_rel_list.append(a_predicate_analogue)        

                    for a_arg_analogue in  all_arguments:
                        arg_role = "-".join(a_arg_analogue.enc_self.split("-")[1:])
                        if not re.match("ARG[0-9]+",arg_role):
                            '''
                            only keep the core roles
                            '''
                            continue
                        role_rel_list.append(a_arg_analogue)
                        core_subtree, r_subtrees, c_subtrees = a_arg_analogue.get_subtree_tuple()

                    sort_by_arg_id = sorted(role_rel_list, key=lambda x:"-".join(x.enc_self.split("-")[1:]))
                    
                    
#                    print a_tree_document[a_predicate_analogue.sentence_index]
#                    print a_predicate_analogue.id,current_pred.tag,current_pred.word
#                    print a_prop.enc_prop
                    
                    if len(a_prop_document) > 1:        
                        for b_prop in a_prop_document[a_index+1:]:
                            b_role_rel_list = []
                            b_doc_id, b_sent_id = b_prop.enc_prop.split()[0:2]
                            b_doc_genre=b_doc_id.split("/")[0]
                            b_doc_fileid=b_doc_id.split("@")[0].split("/")[-1]
                            b_file_id=b_doc_genre+"_"+b_doc_fileid+"_"+b_sent_id
                            
                            
                            b_predicate_analogue = b_prop.predicate
                            b_pred_lemma_sense_num, b_pred_type, b_pred_token_index, b_sentence_index, b_document_id = b_predicate_analogue.id.split("@")[:5]
                            
                            if b_file_id in dev_test_id_dict or a_predicate_analogue.sentence_index != b_predicate_analogue.sentence_index:
                                continue  
                            
                            b_leaves = a_tree_document[b_predicate_analogue.sentence_index].leaves()
                            b_pred_token_index = b_predicate_analogue.token_index
                            b_current_pred = b_leaves[int(b_pred_token_index)]

                            if not self.isPredicate(current_pred) or not self.isPredicate(b_current_pred):
                                continue 
                            
                            b_all_arguments = b_prop.argument_analogues
                            b_role_rel_list.append(b_predicate_analogue)
                            for a_arg_analogue in b_all_arguments:
                                arg_role = "-".join(a_arg_analogue.enc_self.split("-")[1:])
                                if not re.match("ARG[0-9]+",arg_role):
                                    continue
                                b_role_rel_list.append(a_arg_analogue)
                            b_sort_by_arg_id = sorted(b_role_rel_list, key=lambda x:"-".join(x.enc_self.split("-")[1:]))
                            
                            if self.isControl(a_prop, b_prop, a_tree_document, head_rules) and self.isInfinitive(b_current_pred):
#                                print a_tree_document[a_predicate_analogue.sentence_index]
#                                print a_prop.enc_prop,current_pred.tag,current_pred.word
#                                print b_prop.enc_prop,b_current_pred.tag,b_current_pred.word
                                
                                a_control_rule = self.getControlRule(a_prop, b_prop,sort_by_arg_id,b_sort_by_arg_id,a_tree_document)
                                
                                if a_control_rule == None:
                                    print "++++++++++++++++++++++false rule"
                                    continue
                                
#                                raw_input("control&infinitive")
                                if control_prev_doc_id != doc_id or control_prev_sent_id != sent_id:
                                    ref_control_output_file.write("# "+doc_id+" "+sent_id+"\n")
                                    ref_control_output_file.write("# "+sent_str+"\n\n")
                                    
                                if a_control_rule not in control_rule_dict:
                                    control_rule_dict[a_pred_rule] = 1
                                else:
                                    control_rule_dict[a_pred_rule] += 1
                                
                                ref_control_output_file.write(a_control_rule+"\n\n")
        
                                control_prev_doc_id = doc_id
                                control_prev_sent_id = sent_id

                    if self.isPredicate(current_pred):

                        a_pred_rule = self.getPredicateRule(a_tree_document, sort_by_arg_id,a_prop)
                        if a_pred_rule == None:
                            print "++++++++++++++++++++++false rule"
                            continue

                        if prev_doc_id != doc_id or prev_sent_id != sent_id:

                            ref_predicate_output_file.write("# "+doc_id+" "+sent_id+"\n")
                            ref_predicate_output_file.write("# "+sent_str+"\n\n")
                        if a_pred_rule not in predicate_dict:
                            predicate_dict[a_pred_rule] = 1
                        else:
                            predicate_dict[a_pred_rule] += 1
                        
                        ref_predicate_output_file.write(a_pred_rule+"\n\n")

                        prev_doc_id = doc_id
                        prev_sent_id = sent_id

                    vbn_pre_inverse_arg_index = self.isPreMod(current_pred,sort_by_arg_id,"VBN")
                    if vbn_pre_inverse_arg_index:
                        vbn_pre_inverse_arg_index = int(vbn_pre_inverse_arg_index.split("_")[1])
                        a_vbn_premod_rule = self.getModRule(a_tree_document,sort_by_arg_id,vbn_pre_inverse_arg_index,"VBN",a_prop)
                        if a_vbn_premod_rule == None:
                            continue
                        if a_vbn_premod_rule not in vbn_premod_dict:
                            vbn_premod_dict[a_vbn_premod_rule] = 1
                        else:
                            vbn_premod_dict[a_vbn_premod_rule] += 1
#                        print a_tree_document[a_predicate_analogue.sentence_index]
#                        print a_prop.enc_prop
#                        print a_vbn_premod_rule
#                        if len(sort_by_arg_id) > 2:
#                            raw_input("vbn")
                 
        
                    vbg_pre_inverse_arg_index = self.isPreMod(current_pred,sort_by_arg_id,"VBG")
                    if vbg_pre_inverse_arg_index:
                        vbg_pre_inverse_arg_index = int(vbg_pre_inverse_arg_index.split("_")[1])
                        a_vbg_premod_rule = self.getModRule(a_tree_document,sort_by_arg_id,vbg_pre_inverse_arg_index,"VBG",a_prop)
                        if a_vbg_premod_rule == None:
                            continue
                        if a_vbg_premod_rule not in vbg_premod_dict:
                            vbg_premod_dict[a_vbg_premod_rule] = 1
                        else:
                            vbg_premod_dict[a_vbg_premod_rule] += 1
#                        print a_tree_document[a_predicate_analogue.sentence_index]
#                        print a_prop.enc_prop
#                        print a_vbg_premod_rule
#
#                        if len(sort_by_arg_id) > 2:
#                            raw_input("vbg")
        

                            
            
            ref_predicate_output_file.close()
            ref_control_output_file.close()
            
            predicate_output_file = open(output+".predicate."+gen+"."+prefix+".txt", "w")
            predicate_pickle_file = open(output+".predicate."+gen+"."+prefix+".pickle", "w")
            pickle.dump(predicate_dict, predicate_pickle_file)
            for a_rule in sorted(predicate_dict.iterkeys()):
                predicate_output_file.write(a_rule+"\n")
            predicate_output_file.close()
            predicate_pickle_file.close()
    
         
            vbg_premod_output_file = open(output+".vbgpremod."+gen+"."+prefix+".txt", "w")
            vbg_premod_pickle_file = open(output+".vbgpremod."+gen+"."+prefix+".pickle", "w")
            pickle.dump(vbg_premod_dict, vbg_premod_pickle_file)
            for a_rule in sorted(vbg_premod_dict.iterkeys()):
                vbg_premod_output_file.write(a_rule+"\n")
            vbg_premod_output_file.close()
            vbg_premod_pickle_file.close()
                
            vbn_premod_output_file = open(output+".vbnpremod."+gen+"."+prefix+".txt", "w")
            vbn_premod_pickle_file = open(output+".vbnpremod."+gen+"."+prefix+".pickle", "w")
            pickle.dump(vbn_premod_dict, vbn_premod_pickle_file)
            for a_rule in sorted(vbn_premod_dict.iterkeys()):
                vbn_premod_output_file.write(a_rule+"\n")
            vbn_premod_output_file.close()
            vbn_premod_pickle_file.close()            
        

                            
def main():
    ssm = semSynMap()
    a_ontonotes = ssm.getAOntonotes()
    #dev_test="/nfs/guest/yaqiny/Dropbox/Code/generation/dev_test_id.txt"
    #dev_test="/home/nlg-01/yy_140/generation/Code/generation/dev_test_id.txt"
    dev_test="/Users/yaqin276/Dropbox/Code/generation/dev_test_id.txt"
    he = head()
    #head_rules = he.loadHeadrules("/nfs/guest/yaqiny/Dropbox/Code/OntonotesUtil/ontonotes-db-tool-v0.999b/data/headrules.txt")
    #head_rules = he.loadHeadrules("/home/nlg-01/yy_140/generation/Code/OntonotesUtil/ontonotes-db-tool-v0.999b/data/headrules.txt")
    head_rules = he.loadHeadrules("/Users/yaqin276/Dropbox/Code/OntonotesUtil/ontonotes-db-tool-v0.999b/data/headrules.txt")
    #output_dir="/nfs/guest/yaqiny/Dropbox/Code/generation/rules/prop-anotation/propbank"
    #output_dir="/home/nlg-01/yy_140/generation/Code/generation/rules/prop-anotation/propbank"
    output_dir="/Users/yaqin276/Dropbox/Code/generation/rules/prop-anotation/propbank"
    ssm.traverseTrees(output_dir,a_ontonotes,dev_test,head_rules)

    
if __name__=="__main__":
    main()
