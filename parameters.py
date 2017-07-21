"""
Parameters for RL Network
Nicolas Masse, Gregory Grant, Catherine Lee, Varun Iyer
2017/7/20
"""

import numpy as np
import itertools

print("\n--> Loading parameters...")

##############################
### Independent parameters ###
##############################

global par

par = {
    # Setup parameters
    'task_name'             : None,
    'processor_affinity'    : [0, 1],
    'save_dir'              : './savedir/',
    'load_previous_model'   : False,
    'processor_affinity'    : [0, 1],

    # Network configuration
    'synapse_config'    : None,      # Full is 'std_stf'
    'exc_inh_prop'      : 0.8,       # Literature 0.8, for EI off 1
    'use_dendrites'     : False,
    'use_stim_soma'     : False,
    'df_num'            : '0008',    # Designates which dendrite function to use

    # hidden layer shape
    'n_input'           : 50,
    'n_decision'        : 50,
    'n_value'           : 50,
    'den_per_unit'      : 8,

    # Timings and rates
    'dt'                        : 20,
    'learning_rate'             : 5e-3,
    'membrane_time_constant'    : 50,
    'dendrite_time_constant'    : 200,
    'connection_prob'           : 0.5,         # Usually 1
    'mask_connectivity'         : 1.0,

    # Variance values
    'clip_max_grad_val' : 0.25,
    'input_mean'        : 0,
    'input_sd'          : 0.1/10,
    'noise_sd'          : 0.5/10,

    # Tuning function data
    'tuning_height'     : 1,        # magnitutde scaling factor for von Mises
    'kappa'             : 1,        # concentration scaling factor for von Mises
    'catch_rate'        : 0.2,
    'match_rate'        : 0.5,      # tends a little higher than chosen rate

    # Probe specs
    'probe_trial_pct'   : 0,
    'probe_time'        : 25,

    # Cost parameters/function
    'spike_cost'        : 2e-3,
    'dend_cost'         : 1e-3,
    'wiring_cost'       : 5e-7,
    'loss_function'     : 'MSE',

    # Synaptic plasticity specs
    'tau_fast'          : 200,
    'tau_slow'          : 1500,
    'U_stf'             : 0.15,
    'U_std'             : 0.45,

    # Performance thresholds
    'stop_perf_th'      : 1,
    'stop_error_th'     : 1,

    # Training specification
    'batch_train_size'      : 100,
    'num_train_batches'     : 100,
    'num_test_batches'      : 20,
    'num_iterations'        : 10,
    'iterations_between_outputs'    : 5,        # Ususally 500
    'switch_rule_iteration'         : 5,

    # Save paths and other info
    'save_dir'              : './savedir/',
    'save_notes'            : '',
    'save_fn'               : 'model_data.json',
    'use_checkpoints'   : False,
    'ckpt_save_fn'      : 'model_' + str(0) + '.ckpt',
    'ckpt_load_fn'      : 'model_' + str(0) + '.ckpt',

    # Analysis
    'time_pts'          : [850, 1200],
    'num_category_rule' : 1,
    'roc_vars'          : None,
    'anova_vars'        : ['state_hist', 'dend_hist', 'dend_exc_hist', 'dend_inh_hist'],
    'tuning_vars'       : ['state_hist', 'dend_hist', 'dend_exc_hist', 'dend_inh_hist']
}


##############################
###  Dependent parameters  ###
##############################

def initialize(dims, connection_prob):
    n = np.float32(np.random.gamma(shape=0.25, scale=1.0, size=dims))
    n *= (np.random.rand(*dims) < connection_prob)
    return n

def update_parameters(updates):
    """
    Takes a list of strings and values for updating parameters in the parameter dictionary
    Example: updates = [(key, val), (key, val)]
    """
    for (key, val) in updates:
        par[key] = val

    update_dependencies()

def generate_masks():

    # for input neurons, stimulus tuned will have ID=0, rule/fix tuned will have ID =1
    input_type = np.zeros((par['n_input']), dtype = np.uint8)
    input_type[par['num_stim_tuned']:] = 1

    # for hidden nuerons, EXC will have ID=2, PV will have ID=3, VIP will have ID=4, SOM will have ID=5
    # 50% of INH neurons will be PV, 25% for VIP, SOM
    n = par['num_inh_units']//4
    hidden_type = 2*np.ones((par['n_input']), dtype = np.uint8)
    hidden_type[par['num_exc_units']:par['num_exc_units']+2*n] = 3
    hidden_type[par['num_exc_units']+2*n:par['num_exc_units']+2*3] = 4
    hidden_type[par['num_exc_units']+3*n::] = 5


    connectivity = np.ones((2,6,6)) # dim 0=0 refers to connections to soma, dim 0=1 refers to connections to dendrite
    # to soma
    connectivity[0, 0, 2:4] = 1 # stim tuned will project to EXC,PV
    connectivity[0, 2, 2:4] = 1 # EXC will project to EXC,PV
    connectivity[0, 3, 2:4] = 1 # PV will project to EXC,PV
    connectivity[0, 4, 5] = 1 # VIP will project to SOM

    # to dendrites
    connectivity[1, 0, 2:4] = 1 # stim tuned will project to EXC,PV
    connectivity[1, 1, 2:5] = 1 # rule tuned will project to EXC,PV,VIP
    connectivity[1, 2, 2:4] = 1 # EXC will project to EXC,PV
    connectivity[1, 4, 5] = 1 # VIP will project to SOM
    connectivity[1, 5, 2:4] = 1 # SOM will project to EXC,PV

    par['w_rnn_dend_mask'] = np.zeros((par['hidden_to_hidden_dend_dims']), dtype=np.float32)
    par['w_rnn_soma_mask'] = np.zeros((par['hidden_to_hidden_soma_dims']), dtype=np.float32)

    par['w_env_dend_mask'] = np.zeros((par['input_to_decision_dend_dims']), dtype=np.float32)
    par['w_env_soma_mask'] = np.zeros((par['input_to_decision_soma_dims']), dtype=np.float32)

    par['w_act_to_val_dend_mask'] = np.zeros((par['act_to_val_dend_dims']), dtype=np.float32)
    par['w_act_to_val_soma_mask'] = np.zeros((par['act_to_val_soma_dims']), dtype=np.float32)

    par['w_dec_to_val_dend_mask'] = np.zeros((par['decision_to_val_dend_dims']), dtype=np.float32)
    par['w_dec_to_val_soma_mask'] = np.zeros((par['decision_to_val_soma_dims']), dtype=np.float32)

    # input to decision
    for source in range(par['n_input']):
        for target in range(par['n_decision']):
            par['w_env_dend_mask'][target,:,source] = connectivity[1,input_type[source],hidden_type[target]]
            par['w_env_soma_mask'][target,source] = connectivity[0,input_type[source],hidden_type[target]]

    # decision to value
    for source in range(par['n_decision']):
        for target in range(par['n_value']):
            par['w_val_dend_mask'][target,:,source] = connectivity[1,input_type[source],hidden_type[target]]
            par['w_val_soma_mask'][target,source] = connectivity[0,input_type[source],hidden_type[target]]

    # action to decision
    for source in range(par['n_output']):
        for target in range(par['n_value']):
            par['w_act_dend_mask'][target,:,source] = connectivity[1,input_type[source],hidden_type[target]]
            par['w_act_soma_mask'][target,source] = connectivity[0,input_type[source],hidden_type[target]]            
 
    # hidden to hidden
    for source in range(par['n_decision']+par['n_value']):
        for target in range(par['n_decision']+par['n_value']):
            par['w_rnn_dend_mask'][target,:,source] = connectivity[1,hidden_type[source],hidden_type[target]]
            par['w_rnn_soma_mask'][target,source] = connectivity[0,hidden_type[source],hidden_type[target]]


def reduce_connectivity():
    # Clamp masks randomly
    r_nh    = range(par['n_hidden'])
    r_dpu   = range(par['den_per_unit'])
    r_nst   = range(par['num_stim_tuned'])
    r_ninst = range(par['n_input']-par['num_stim_tuned'])

    for i, j, k in itertools.product(r_nh, r_dpu, r_nst):
        if np.random.rand() > par['mask_connectivity']:
            par['w_env_dend_mask'][i,j,k] = 0
        if np.random.rand() > par['mask_connectivity'] and j == 0:
            par['w_env_soma_mask'][i,k] = 0

    for i, j, k in itertools.product(r_nh, r_dpu, r_ninst):
        if np.random.rand() > par['mask_connectivity']:
            par['w_td_dend_mask'][i,j,k] = 0
        if np.random.rand() > par['mask_connectivity'] and j == 0:
            par['w_td_soma_mask'][i,k] = 0

    for i, j, k in itertools.product(r_nh, r_dpu, r_nh):
        if np.random.rand() > par['mask_connectivity']:
            par['w_rnn_dend_mask'][i,j,k] = 0
        if np.random.rand() > par['mask_connectivity'] and j == 0:
            par['w_rnn_soma_mask'][i,k] = 0


def spectral_radius(A):
    """
    Compute the spectral radius of each dendritic dimension of a weight array,
    and normalize using square room of the sum of squares of those radii.
    """
    if A.ndim == 2:
        return np.max(abs(np.linalg.eigvals(A)))
    elif A.ndim == 3:
        # Assumes the second axis is the target (for dendritic setup)
        r = 0
        for n in range(np.shape(A)[1]):
            r = r + np.max(abs(np.linalg.eigvals(np.squeeze(A[:,n,:]))))

        return r / np.shape(A)[1]


def update_dependencies():
    """
    Updates all parameter dependencies
    """

    # Projected number of trials to take place
    par['projected_num_trials'] = par['batch_train_size']*par['num_train_batches']*par['num_iterations']

    # General network shape
    par['shape'] = (par['n_input'], par['n_decision'], par['n_output'])

    # Possible rules based on rule type values
    par['possible_rules'] = [par['num_RFs'], par['num_rules']]
    # Number of rules - used in input tuning
    #par['num_rules'] = len(par['possible_rules'])

    # Sets the number of accessible allowed fields, if equal, all allowed fields
    # are accessible, but no more than those.
    par['num_active_fields'] = len(par['allowed_fields'])
    # Checks to ensure valid receptor fields
    if len(par['allowed_fields']) < par['num_active_fields']:
        print("ERROR: More active fields than allowed receptor fields.")
        quit()
    elif par['num_active_fields'] <= 0:
        print("ERROR: Must have 1 or more active receptor fields.")
        quit()

    # If num_inh_units is set > 0, then neurons can be either excitatory or
    # inihibitory; is num_inh_units = 0, then the weights projecting from
    # a single neuron can be a mixture of excitatory or inhibitory
    if par['exc_inh_prop'] < 1:
        par['EI'] = True
    else:
        par['EI']  = False

    par['num_exc_units'] = int(np.round(par['n_decision']*par['exc_inh_prop']))
    par['num_inh_units'] = par['n_decision'] - par['num_exc_units']

    par['EI_list'] = np.ones(par['n_decision'], dtype=np.float32)
    par['EI_list'][-par['num_inh_units']:] = -1.

    par['EI_matrix'] = np.diag(par['EI_list'])

    par['EI_list_d_exc'] = np.ones(par['n_decision'], dtype=np.float32)
    par['EI_list_d_inh'] = np.ones(par['n_decision'], dtype=np.float32)

    par['EI_list_d_exc'][-par['num_inh_units']:] = 0.
    par['EI_list_d_inh'][:par['num_exc_units']] = 0.

    par['EI_matrix_d_exc'] = np.diag(par['EI_list_d_exc'])
    par['EI_matrix_d_inh'] = np.diag(par['EI_list_d_inh'])

    # The previous exc_inh_prop addresses soma-to-soma interactions, but this
    # EI matrix addresses soma-to-dendrite interactions.  It follows the same
    # setup process, however.

    # [par['n_decision'], par['den_per_unit'], par['n_decision']]
    par['num_exc_dends'] = int(np.round(par['den_per_unit']))

    # Membrane time constant of RNN neurons
    par['alpha_neuron'] = par['dt']/par['membrane_time_constant']
    # The standard deviation of the Gaussian noise added to each RNN neuron
    # at each time step
    par['noise_sd'] = np.sqrt(2*par['alpha_neuron'])*par['noise_sd']

    # Dendrite time constant for dendritic branches
    par['alpha_dendrite'] = par['dt']/par['dendrite_time_constant']


    ####################################################################
    ### Setting up assorted intial weights, biases, and other values ###
    ####################################################################

    par['h_init'] = 0.1*np.ones((par['n_decision']+par['n_value'], par['batch_train_size']), dtype=np.float32)
    par['d_init'] = 0.1*np.ones((par['n_decision']+par['n_value'], par['den_per_unit'], par['batch_train_size']), dtype=np.float32)

    par['input_to_decision_dend_dims'] = [par['n_decision'], par['den_per_unit'], par['n_input']]
    par['input_to_decision_soma_dims'] = [par['n_decision'], par['n_input']]

    par['decision_to_val_dend_dims'] = [par['n_value'], par['den_per_unit'], par['n_decision']]
    par['decision_to_val_soma_dims'] = [par['n_value'], par['n_decision']]

    par['act_to_val_dend_dims'] = [par['n_value'], par['den_per_unit'], par['n_output']]
    par['act_to_val_soma_dims'] = [par['n_value'], par['n_output']]

    par['hidden_to_hidden_dend_dims'] = [par['n_decision']+par['n_value'], par['den_per_unit'], par['n_decision']+par['n_value']]
    par['hidden_to_hidden_soma_dims'] = [par['n_decision']+par['n_value'], par['n_decision']+par['n_value']]

    # Generate random masks
    generate_masks()

    if par['mask_connectivity'] < 1:
        reduce_connectivity()

    # Initialize input weights
    par['w_env_dend0'] = initialize(par['input_to_decision_dend_dims'], par['connection_prob'])
    par['w_env_soma0'] = initialize(par['input_to_decision_soma_dims'], par['connection_prob'])

    par['w_dec_to_val_dend0'] = initialize(par['decision_to_val_dend_dims'], par['connection_prob'])
    par['w_dec_to_val_soma0'] = initialize(par['decision_to_val_soma_dims'], par['connection_prob'])

    par['w_act_to_val_dend0'] = initialize(par['act_to_val_dend_dims'], par['connection_prob'])
    par['w_act_to_val_soma0'] = initialize(par['act_to_val_soma_dims'], par['connection_prob'])


    par['w_env_dend0'] *= par['w_env_dend_mask']
    par['w_env_soma0'] *= par['w_env_soma_mask']

    par['w_dec_to_val_dend0'] *= par['w_dec_to_val_dend_mask']
    par['w_dec_to_val_soma0'] *= par['w_dec_to_val_soma_mask']

    par['w_act_to_val_dend0'] *= par['w_act_to_val_dend_mask']
    par['w_act_to_val_soma0'] *= par['w_act_to_val_soma_mask']

    # Initialize starting recurrent weights
    # If excitatory/inhibitory neurons desired, initializes with random matrix with
    #   zeroes on the diagonal
    # If not, initializes with a diagonal matrix
    if par['EI']:
        par['w_rnn_dend0'] = initialize(par['hidden_to_hidden_dend_dims'], par['connection_prob'])
        par['w_rnn_soma0'] = initialize(par['hidden_to_hidden_soma_dims'], par['connection_prob'])
        #par['w_rnn_dend_mask'] = np.ones((par['hidden_to_hidden_dend_dims']), dtype=np.float32)
        #par['w_rnn_soma_mask'] = np.ones((par['hidden_to_hidden_soma_dims']), dtype=np.float32) - np.eye(par['n_decision'])

        for i in range(par['n_decision']+par['n_value']):
            par['w_rnn_soma0'][i,i] = 0
            #par['w_rnn_dend_mask'][i,:,i] = 0
            par['w_rnn_dend0'][i,:,i] = 0

    else:
        par['w_rnn_dend0'] = np.zeros(par['hidden_to_hidden_dend_dims'], dtype=np.float32)
        par['w_rnn_soma0'] = np.eye(par['hidden_to_hidden_soma_dims'], dtype=np.float32)

        for i in range(par['n_decision']+par['n_value']):
            par['w_rnn_dend0'][i,:,i] = 1

        #par['w_rnn_dend_mask'] = np.ones((par['hidden_to_hidden_dend_dims']), dtype=np.float32)
        #par['w_rnn_soma_mask'] = np.ones((par['hidden_to_hidden_soma_dims']), dtype=np.float32)

    par['w_rnn_dend0'] *= par['w_rnn_dend_mask']
    par['w_rnn_soma0'] *= par['w_rnn_soma_mask']

    # Initialize starting recurrent biases
    # Note that the second dimension in the bias initialization term can be either
    # 1 or self.params['batch_train_size'].
    set_to_one = True
    par['bias_dim'] = (1 if set_to_one else par['batch_train_size'])
    par['b_rnn0'] = np.zeros((par['n_decision']+par['n_value'], par['bias_dim']), dtype=np.float32)

    # Effective synaptic weights are stronger when no short-term synaptic plasticity
    # is used, so the strength of the recurrent weights is reduced to compensate
    if par['synapse_config'] == None:
        par['w_rnn_dend0'] /= (2*spectral_radius(par['w_rnn_dend0']))
        par['w_rnn_soma0'] /= (2*spectral_radius(par['w_rnn_soma0']))

    # Initialize output weights and biases
    par['w_out0'] =initialize([par['n_output'], par['n_decision']], par['connection_prob'])

    par['b_out0'] = np.zeros((par['n_output'], 1), dtype=np.float32)
    par['w_out_mask'] = np.ones((par['n_output'], par['n_decision']), dtype=np.float32)

    if par['EI']:
        par['ind_inh'] = np.where(par['EI_list'] == -1)[0]
        par['w_out0'][:, par['ind_inh']] = 0
        par['w_out_mask'][:, par['ind_inh']] = 0

    ######################################
    ### Setting up synaptic parameters ###
    ######################################

    # 0 = static
    # 1 = facilitating
    # 2 = depressing

    par['synapse_type'] = np.zeros(par['n_decision']+par['n_value'], dtype=np.int8)

    # only facilitating synapses
    if par['synapse_config'] == 'stf':
        par['synapse_type'] = np.ones(par['n_decision']+par['n_value'], dtype=np.int8)

    # only depressing synapses
    elif par['synapse_config'] == 'std':
        par['synapse_type'] = 2*np.ones(par['n_decision']+par['n_value'], dtype=np.int8)

    # even numbers facilitating, odd numbers depressing
    elif par['synapse_config'] == 'std_stf':
        par['synapse_type'] = np.ones(par['n_decision']+par['n_value'], dtype=np.int8)
        par['ind'] = range(1,par['n_decision']+par['n_value'],2)
        par['synapse_type'][par['ind']] = 2

    par['alpha_stf'] = np.ones((par['n_decision']+par['n_value'], 1), dtype=np.float32)
    par['alpha_std'] = np.ones((par['n_decision']+par['n_value'], 1), dtype=np.float32)
    par['U'] = np.ones((par['n_decision']+par['n_value'], 1), dtype=np.float32)

    # initial synaptic values
    par['syn_x_init'] = np.zeros((par['n_decision']+par['n_value'], par['batch_train_size']), dtype=np.float32)
    par['syn_u_init'] = np.zeros((par['n_decision']+par['n_value'], par['batch_train_size']), dtype=np.float32)

    for i in range(par['n_decision']+par['n_value']):
        if par['synapse_type'][i] == 1:
            par['alpha_stf'][i,0] = par['dt']/par['tau_slow']
            par['alpha_std'][i,0] = par['dt']/par['tau_fast']
            par['U'][i,0] = 0.15
            par['syn_x_init'][i,:] = 1
            par['syn_u_init'][i,:] = par['U'][i,0]

        elif par['synapse_type'][i] == 2:
            par['alpha_stf'][i,0] = par['dt']/par['tau_fast']
            par['alpha_std'][i,0] = par['dt']/par['tau_slow']
            par['U'][i,0] = 0.45
            par['syn_x_init'][i,:] = 1
            par['syn_u_init'][i,:] = par['U'][i,0]


##############################
###  Parameter functions  ####
##############################
def set_task_profile():
    """
    Depending on the stimulus type, sets the network
    to the appropriate configuration
    """
    pass


set_task_profile()
update_dependencies()
print("--> Parameters successfully loaded.\n")


